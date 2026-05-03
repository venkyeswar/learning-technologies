# 07 · RAG — Converting PDFs & SQL Data into Searchable Documents

> **Goal:** Understand how to take real-world data sources (PDFs, SQL databases) and convert them into Elasticsearch documents — the foundation of RAG (Retrieval-Augmented Generation) and semantic search.

---

## What Is RAG?

**RAG = Retrieval-Augmented Generation**

Instead of relying solely on an LLM's training data, you:

1. **Retrieve** relevant documents from your own knowledge base (Elasticsearch)
2. **Augment** the LLM's prompt with those retrieved chunks
3. **Generate** an answer grounded in your data

```
User question
      │
      ▼
┌─────────────────┐
│  Elasticsearch  │  ← your knowledge base
│  (search/knn)   │
└────────┬────────┘
         │  top-k relevant chunks
         ▼
┌─────────────────────────────────────────────┐
│  Prompt = "Answer using this context:\n"    │
│           + chunks + "\nQuestion: " + query │
└────────┬────────────────────────────────────┘
         │
         ▼
    LLM (Claude / GPT)
         │
         ▼
    Grounded Answer
```

---

## The Chunking Problem

LLMs have context limits. You can't stuff an entire 100-page PDF into a prompt. You split documents into **chunks** and store each chunk as a separate Elasticsearch document.

```
PDF: "Machine Learning Guide" (100 pages)
        ↓  chunk(size=500, overlap=50)
Chunk 1: "Chapter 1: Introduction to ML..."  (chars 0-500)
Chunk 2: "...to ML. Supervised learning..."   (chars 450-950)  ← overlap
Chunk 3: "...learning means training with..."  (chars 900-1400)
...
Chunk N: "...Conclusion and references..."
```

**Why overlap?** To preserve context at chunk boundaries.

---

## Part A — PDF to Elasticsearch

### Install Dependencies

```bash
pip install pdfplumber pypdf elasticsearch sentence-transformers
```

### Step 1: Extract Text from PDF

```python
import pdfplumber
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text page by page from a PDF.
    Returns list of {"page": int, "text": str} dicts.
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page": page_num,
                    "text": text.strip()
                })
    return pages

pages = extract_text_from_pdf("machine_learning_guide.pdf")
print(f"Extracted {len(pages)} pages")
```

### Step 2: Chunk the Text

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks of ~chunk_size characters.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to end at a sentence boundary
        if end < text_len:
            last_period = text.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap  # overlap for context continuity

    return chunks


def pdf_to_chunks(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Full pipeline: PDF → pages → chunks with metadata.
    """
    filename = Path(pdf_path).stem
    pages = extract_text_from_pdf(pdf_path)
    all_chunks = []
    chunk_id = 0

    for page_data in pages:
        chunks = chunk_text(page_data['text'], chunk_size, overlap)
        for chunk in chunks:
            all_chunks.append({
                "chunk_id": chunk_id,
                "source": filename,
                "source_type": "pdf",
                "page": page_data['page'],
                "content": chunk,
                "content_length": len(chunk)
            })
            chunk_id += 1

    print(f"Created {len(all_chunks)} chunks from '{pdf_path}'")
    return all_chunks
```

### Step 3: Index Chunks into Elasticsearch

```python
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch("http://localhost:9200")
CHUNKS_INDEX = "document_chunks"

def create_chunks_index():
    mapping = {
        "mappings": {
            "properties": {
                "chunk_id":      {"type": "integer"},
                "source":        {"type": "keyword"},
                "source_type":   {"type": "keyword"},
                "page":          {"type": "integer"},
                "content":       {"type": "text", "analyzer": "english"},
                "content_length":{"type": "integer"},
                "embedding":     {
                    "type": "dense_vector",
                    "dims": 384,             # depends on your model
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    if not es.indices.exists(index=CHUNKS_INDEX):
        es.indices.create(index=CHUNKS_INDEX, body=mapping)
        print(f"Index '{CHUNKS_INDEX}' created.")


def index_chunks(chunks: list[dict], embeddings=None):
    """Index chunks, optionally with embeddings."""
    actions = []
    for i, chunk in enumerate(chunks):
        doc = chunk.copy()
        if embeddings is not None:
            doc["embedding"] = embeddings[i].tolist()
        actions.append({
            "_index": CHUNKS_INDEX,
            "_source": doc
        })

    success, failed = helpers.bulk(es, actions, raise_on_error=False)
    print(f"Indexed {success} chunks, {len(failed)} failed")


# Full pipeline
create_chunks_index()
chunks = pdf_to_chunks("machine_learning_guide.pdf")
index_chunks(chunks)
```

---

## Part B — SQL Database to Elasticsearch

### Concept

```
PostgreSQL Table: products
  id | name | description | price | category | stock
  ─────────────────────────────────────────────────────
  1  | "Nike Air Max" | "Running shoe..." | 8999 | "Shoes" | 50
  2  | "Levi's 501"   | "Classic jeans..." | 4999 | "Jeans" | 120

                  ↓  sync to ES

Elasticsearch Index: products
  { "_id": "1", "name": "Nike Air Max", "description": "...", "price": 8999, ... }
  { "_id": "2", "name": "Levi's 501", "description": "...", "price": 4999, ... }
```

### Install

```bash
pip install psycopg2-binary sqlalchemy elasticsearch
# Or for SQLite (no install needed): import sqlite3
```

### SQLite Example (No Server Needed)

```python
import sqlite3
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch("http://localhost:9200")

# --- Create SQLite DB and sample data ---
conn = sqlite3.connect("products.db")
conn.row_factory = sqlite3.Row   # access columns by name
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL,
        category TEXT,
        brand TEXT,
        stock INTEGER,
        created_at TEXT
    )
""")

sample_products = [
    (1, "Nike Air Max 270", "Lightweight running shoe with Max Air cushioning", 8999, "Shoes", "Nike", 50, "2023-01-15"),
    (2, "Adidas Ultraboost 22", "Premium running shoe with Boost technology", 12999, "Shoes", "Adidas", 30, "2023-03-20"),
    (3, "Levi's 501 Original Jeans", "Classic straight-fit jeans in dark wash", 4999, "Jeans", "Levi's", 120, "2022-11-10"),
    (4, "Sony WH-1000XM5", "Industry-leading noise-cancelling headphones", 24999, "Electronics", "Sony", 15, "2023-05-01"),
    (5, "Apple AirPods Pro 2", "Active noise cancellation with Adaptive Transparency", 19999, "Electronics", "Apple", 40, "2023-09-18"),
]

cursor.executemany(
    "INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?)",
    sample_products
)
conn.commit()
print("SQLite DB ready.")


# --- Sync to Elasticsearch ---

def create_products_index():
    mapping = {
        "mappings": {
            "properties": {
                "name":        {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "description": {"type": "text"},
                "price":       {"type": "float"},
                "category":    {"type": "keyword"},
                "brand":       {"type": "keyword"},
                "stock":       {"type": "integer"},
                "created_at":  {"type": "date", "format": "yyyy-MM-dd"}
            }
        }
    }
    if not es.indices.exists(index="products"):
        es.indices.create(index="products", body=mapping)
        print("Products index created.")


def sync_sql_to_elasticsearch(batch_size: int = 100):
    """
    Read from SQL and bulk-index into Elasticsearch.
    For large tables, process in batches.
    """
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    actions = []
    for row in rows:
        doc = dict(row)
        doc_id = str(doc.pop("id"))  # use SQL primary key as ES _id

        actions.append({
            "_index": "products",
            "_id": doc_id,
            "_source": doc
        })

        if len(actions) >= batch_size:
            helpers.bulk(es, actions)
            actions = []

    if actions:  # flush remaining
        helpers.bulk(es, actions)

    print(f"Synced {len(rows)} products to Elasticsearch.")


create_products_index()
sync_sql_to_elasticsearch()
es.indices.refresh(index="products")

# Verify
count = es.count(index="products")
print(f"Products in ES: {count['count']}")
```

### PostgreSQL Example

```python
import psycopg2
from elasticsearch import helpers

def sync_postgres_to_es(pg_conn_string: str, table: str, es_index: str, batch_size=500):
    """Generic function to sync any PostgreSQL table to Elasticsearch."""
    conn = psycopg2.connect(pg_conn_string)
    conn.set_session(readonly=True)
    cursor = conn.cursor()

    # Get column names
    cursor.execute(f"SELECT * FROM {table} LIMIT 0")
    columns = [desc[0] for desc in cursor.description]

    # Stream rows in batches
    cursor.execute(f"SELECT * FROM {table}")

    actions = []
    total = 0

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        for row in rows:
            doc = dict(zip(columns, row))
            doc_id = str(doc.get("id") or doc.get("_id"))

            actions.append({
                "_index": es_index,
                "_id": doc_id,
                "_source": {k: v for k, v in doc.items() if k not in ("id", "_id")}
            })

        helpers.bulk(es, actions)
        total += len(actions)
        actions = []
        print(f"  synced {total} rows...")

    cursor.close()
    conn.close()
    print(f"Done. Total synced: {total} rows from '{table}' → '{es_index}'")
```

---

## Part C — Semantic Search with Embeddings

For RAG, you often want **semantic search** (find similar meaning, not just matching keywords).

```bash
pip install sentence-transformers
```

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim, fast & good

def generate_embeddings(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    return model.encode(texts, show_progress_bar=True)


def index_chunks_with_embeddings(chunks: list[dict]):
    """Index chunks WITH semantic embeddings for vector search."""
    texts = [chunk["content"] for chunk in chunks]
    embeddings = generate_embeddings(texts)

    actions = []
    for i, chunk in enumerate(chunks):
        doc = chunk.copy()
        doc["embedding"] = embeddings[i].tolist()
        actions.append({"_index": CHUNKS_INDEX, "_source": doc})

    helpers.bulk(es, actions)
    print(f"Indexed {len(chunks)} chunks with embeddings.")


def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Semantic search using vector similarity (kNN).
    Finds chunks that are semantically similar to the query.
    """
    query_embedding = model.encode([query])[0].tolist()

    response = es.search(
        index=CHUNKS_INDEX,
        knn={
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 10
        },
        _source=["content", "source", "page"]
    )

    return [
        {
            "score": hit["_score"],
            "content": hit["_source"]["content"],
            "source": hit["_source"]["source"],
            "page": hit["_source"].get("page")
        }
        for hit in response["hits"]["hits"]
    ]


def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Hybrid search = keyword (BM25) + semantic (kNN) combined.
    Best of both worlds for RAG.
    """
    query_embedding = model.encode([query])[0].tolist()

    response = es.search(
        index=CHUNKS_INDEX,
        query={
            "match": {"content": query}   # keyword search
        },
        knn={
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 10,
            "boost": 0.5   # weight of semantic score
        },
        size=top_k
    )

    return [
        {
            "score": hit["_score"],
            "content": hit["_source"]["content"],
            "source": hit["_source"]["source"],
        }
        for hit in response["hits"]["hits"]
    ]
```

---

## The Full RAG Query Loop

```python
def rag_query(user_question: str, llm_fn) -> str:
    """
    1. Retrieve relevant chunks from Elasticsearch
    2. Build a prompt with context
    3. Call LLM and return grounded answer
    """
    # Step 1: Retrieve
    chunks = hybrid_search(user_question, top_k=5)
    context = "\n\n---\n\n".join([c["content"] for c in chunks])

    # Step 2: Build prompt
    prompt = f"""Answer the question based ONLY on the following context.
If the answer isn't in the context, say "I don't know based on available documents."

Context:
{context}

Question: {user_question}

Answer:"""

    # Step 3: Generate (plug in your LLM here)
    answer = llm_fn(prompt)
    return answer
```

---

## Summary: Data Source → Elasticsearch

```
PDF File
  └─► extract pages (pdfplumber)
  └─► chunk text (500 chars, 50 overlap)
  └─► [optional] generate embeddings
  └─► bulk index to ES

SQL Table
  └─► SELECT * FROM table (in batches)
  └─► map row → JSON document
  └─► use primary key as _id
  └─► bulk index to ES

Text/JSON Files
  └─► parse file
  └─► create document per record
  └─► bulk index to ES
```

---

## Reference Links

- [Dense vector field](https://www.elastic.co/guide/en/elasticsearch/reference/current/dense-vector.html)
- [kNN search](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)
- [sentence-transformers models](https://www.sbert.net/docs/pretrained_models.html)
- [pdfplumber](https://github.com/jsvine/pdfplumber)

---

**← Previous:** [06 · Aggregations](./06_aggregations.md)  
**Next →** [08 · FastAPI Project](./08_fastapi_project.md)
