from elasticsearch import Elasticsearch, helpers
from app.config import get_settings
from typing import Optional

settings = get_settings()


def get_es_client() -> Elasticsearch:
    """Return a connected Elasticsearch client."""
    return Elasticsearch(settings.elasticsearch_url)


# ─── Index Setup ─────────────────────────────────────────────────────────────

PRODUCTS_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "product_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "name": {
                "type": "text",
                "analyzer": "product_analyzer",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "description": {"type": "text", "analyzer": "product_analyzer"},
            "price":       {"type": "float"},
            "category":    {"type": "keyword"},
            "brand":       {"type": "keyword"},
            "rating":      {"type": "float"},
            "stock":       {"type": "integer"},
            "tags":        {"type": "keyword"},
            "image_url":   {"type": "keyword", "index": False}
        }
    }
}

CHUNKS_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "chunk_id":       {"type": "integer"},
            "source":         {"type": "keyword"},
            "source_type":    {"type": "keyword"},
            "page":           {"type": "integer"},
            "content":        {"type": "text", "analyzer": "english"},
            "content_length": {"type": "integer"},
            "embedding": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}


def setup_indices(es: Elasticsearch):
    """Create indices with mappings if they don't exist."""
    for index_name, mapping in [
        (settings.products_index, PRODUCTS_MAPPING),
        (settings.chunks_index, CHUNKS_MAPPING),
    ]:
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name, body=mapping)
            print(f"✅ Created index: '{index_name}'")
        else:
            print(f"ℹ️  Index already exists: '{index_name}'")


# ─── Product Operations ───────────────────────────────────────────────────────

def index_products(es: Elasticsearch, products: list[dict]) -> tuple[int, int]:
    """Bulk index a list of products. Returns (success_count, fail_count)."""
    actions = [
        {
            "_index": settings.products_index,
            "_id": str(p.get("id", i)),
            "_source": {k: v for k, v in p.items() if k != "id"}
        }
        for i, p in enumerate(products)
    ]
    success, failed = helpers.bulk(es, actions, raise_on_error=False)
    es.indices.refresh(index=settings.products_index)
    return success, len(failed)


def search_products(
    es: Elasticsearch,
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "relevance",
    sort_order: str = "desc",
) -> dict:
    """Full-featured product search with filters, facets, and pagination."""

    # Build query
    must_clauses = []
    filter_clauses = []

    if query:
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["name^3", "description", "tags^2", "brand"],
                "fuzziness": "AUTO",
                "type": "best_fields"
            }
        })

    if category:
        filter_clauses.append({"term": {"category": category}})

    if brand:
        filter_clauses.append({"term": {"brand": brand}})

    price_range = {}
    if min_price is not None:
        price_range["gte"] = min_price
    if max_price is not None:
        price_range["lte"] = max_price
    if price_range:
        filter_clauses.append({"range": {"price": price_range}})

    if min_rating is not None:
        filter_clauses.append({"range": {"rating": {"gte": min_rating}}})

    es_query = {
        "bool": {
            "must": must_clauses if must_clauses else [{"match_all": {}}],
            "filter": filter_clauses
        }
    }

    # Build sort
    sort = []
    if sort_by == "price":
        sort.append({"price": {"order": sort_order}})
    elif sort_by == "rating":
        sort.append({"rating": {"order": sort_order}})
    else:
        sort.append("_score")

    # Aggregations for facets
    aggs = {
        "categories": {
            "terms": {"field": "category", "size": 20}
        },
        "brands": {
            "terms": {"field": "brand", "size": 20}
        },
        "price_stats": {
            "stats": {"field": "price"}
        },
        "avg_rating": {
            "avg": {"field": "rating"}
        }
    }

    response = es.search(
        index=settings.products_index,
        query=es_query,
        sort=sort,
        aggs=aggs,
        size=page_size,
        from_=(page - 1) * page_size,
        _source=True
    )

    total = response['hits']['total']['value']
    results = []
    for hit in response['hits']['hits']:
        doc = hit['_source']
        doc['_id'] = hit['_id']
        doc['_score'] = hit.get('_score')
        results.append(doc)

    agg_data = response['aggregations']
    facets = {
        "categories": [
            {"key": b["key"], "count": b["doc_count"]}
            for b in agg_data["categories"]["buckets"]
        ],
        "brands": [
            {"key": b["key"], "count": b["doc_count"]}
            for b in agg_data["brands"]["buckets"]
        ],
        "price_stats": agg_data["price_stats"],
        "avg_rating": agg_data["avg_rating"]["value"],
    }

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": results,
        "facets": facets
    }


def get_product_by_id(es: Elasticsearch, product_id: str) -> Optional[dict]:
    """Retrieve a single product by its ID."""
    try:
        response = es.get(index=settings.products_index, id=product_id)
        doc = response['_source']
        doc['_id'] = response['_id']
        return doc
    except Exception:
        return None


# ─── Chunk Operations ─────────────────────────────────────────────────────────

def index_chunks(es: Elasticsearch, chunks: list[dict]) -> tuple[int, int]:
    """Bulk index document chunks (with embeddings if provided)."""
    actions = [
        {"_index": settings.chunks_index, "_source": chunk}
        for chunk in chunks
    ]
    success, failed = helpers.bulk(es, actions, raise_on_error=False)
    es.indices.refresh(index=settings.chunks_index)
    return success, len(failed)


def keyword_search_chunks(
    es: Elasticsearch,
    query: str,
    source_filter: Optional[str] = None,
    top_k: int = 5
) -> list[dict]:
    """BM25 keyword search over document chunks."""
    filter_clauses = []
    if source_filter:
        filter_clauses.append({"term": {"source": source_filter}})

    response = es.search(
        index=settings.chunks_index,
        query={
            "bool": {
                "must": [{"match": {"content": query}}],
                "filter": filter_clauses
            }
        },
        size=top_k,
        _source=["content", "source", "page"]
    )

    return [
        {
            "content": h["_source"]["content"],
            "source": h["_source"]["source"],
            "page": h["_source"].get("page"),
            "score": h["_score"]
        }
        for h in response["hits"]["hits"]
    ]


def semantic_search_chunks(
    es: Elasticsearch,
    query_embedding: list[float],
    source_filter: Optional[str] = None,
    top_k: int = 5
) -> list[dict]:
    """kNN vector search over document chunks."""
    knn = {
        "field": "embedding",
        "query_vector": query_embedding,
        "k": top_k,
        "num_candidates": top_k * 10
    }
    if source_filter:
        knn["filter"] = {"term": {"source": source_filter}}

    response = es.search(
        index=settings.chunks_index,
        knn=knn,
        size=top_k,
        _source=["content", "source", "page"]
    )

    return [
        {
            "content": h["_source"]["content"],
            "source": h["_source"]["source"],
            "page": h["_source"].get("page"),
            "score": h["_score"]
        }
        for h in response["hits"]["hits"]
    ]


def hybrid_search_chunks(
    es: Elasticsearch,
    query: str,
    query_embedding: list[float],
    source_filter: Optional[str] = None,
    top_k: int = 5
) -> list[dict]:
    """Hybrid search: BM25 + kNN combined."""
    filter_clauses = []
    if source_filter:
        filter_clauses.append({"term": {"source": source_filter}})

    knn = {
        "field": "embedding",
        "query_vector": query_embedding,
        "k": top_k,
        "num_candidates": top_k * 10,
        "boost": 0.5
    }
    if filter_clauses:
        knn["filter"] = {"bool": {"filter": filter_clauses}}

    response = es.search(
        index=settings.chunks_index,
        query={
            "bool": {
                "must": [{"match": {"content": {"query": query, "boost": 0.5}}}],
                "filter": filter_clauses
            }
        },
        knn=knn,
        size=top_k,
        _source=["content", "source", "page"]
    )

    return [
        {
            "content": h["_source"]["content"],
            "source": h["_source"]["source"],
            "page": h["_source"].get("page"),
            "score": h["_score"]
        }
        for h in response["hits"]["hits"]
    ]
