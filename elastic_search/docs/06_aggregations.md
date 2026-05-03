# 06 · Aggregations & Analytics

> **Goal:** Use aggregations to compute statistics, group data, and build faceted search — like a GROUP BY in SQL but much more powerful.

---

## What Are Aggregations?

Aggregations let you compute summaries over your data — counts, averages, histograms, top values — all in a single query. Think of them as the Elasticsearch equivalent of SQL's `GROUP BY`, `COUNT()`, `AVG()`, etc.

```
SQL:  SELECT genre, COUNT(*) FROM books GROUP BY genre;
ES:   "aggs": { "by_genre": { "terms": { "field": "genre" } } }
```

You can run aggregations **alongside a search query** or on the full dataset.

---

## Aggregation Structure

```python
response = es.search(
    index="books",
    query={...},     # optional — filter which docs to aggregate
    aggs={
        "agg_name": {
            "agg_type": {
                "field": "field_name",
                ...options...
            },
            "aggs": {   # optional nested aggregations
                ...
            }
        }
    },
    size=0   # set to 0 to only get aggregation results, not documents
)

# Access aggregation results
agg_result = response['aggregations']['agg_name']
```

---

## 1. Terms Aggregation (Group By)

Count documents per unique value — perfect for faceted filters.

```python
response = es.search(
    index="books",
    aggs={
        "genres": {
            "terms": {
                "field": "genre",   # must be keyword type
                "size": 10          # top N terms
            }
        }
    },
    size=0
)

for bucket in response['aggregations']['genres']['buckets']:
    print(f"{bucket['key']}: {bucket['doc_count']} books")

# Output:
# Programming: 3 books
# Machine Learning: 1 book
```

---

## 2. Metric Aggregations

Compute statistics on numeric fields:

```python
response = es.search(
    index="books",
    aggs={
        "avg_rating":   {"avg":   {"field": "rating"}},
        "max_rating":   {"max":   {"field": "rating"}},
        "min_rating":   {"min":   {"field": "rating"}},
        "total_books":  {"value_count": {"field": "rating"}},
        "rating_stats": {"stats": {"field": "rating"}}  # all stats at once
    },
    size=0
)

aggs = response['aggregations']
print(f"Average rating: {aggs['avg_rating']['value']:.2f}")
print(f"Max rating: {aggs['max_rating']['value']}")
print(f"Stats: {aggs['rating_stats']}")

# Stats output: { "count": 4, "min": 4.4, "max": 4.7, "avg": 4.55, "sum": 18.2 }
```

---

## 3. Range Aggregation

Group documents into defined ranges:

```python
response = es.search(
    index="books",
    aggs={
        "rating_ranges": {
            "range": {
                "field": "rating",
                "ranges": [
                    {"to": 4.0, "key": "below 4"},
                    {"from": 4.0, "to": 4.5, "key": "4.0 - 4.5"},
                    {"from": 4.5, "key": "above 4.5"}
                ]
            }
        }
    },
    size=0
)

for bucket in response['aggregations']['rating_ranges']['buckets']:
    print(f"{bucket['key']}: {bucket['doc_count']} books")
```

---

## 4. Date Histogram Aggregation

Group documents by time intervals — perfect for time-series data.

```python
response = es.search(
    index="books",
    aggs={
        "books_per_year": {
            "date_histogram": {
                "field": "published_at",
                "calendar_interval": "year",   # year, month, week, day
                "format": "yyyy"
            }
        }
    },
    size=0
)

for bucket in response['aggregations']['books_per_year']['buckets']:
    if bucket['doc_count'] > 0:
        print(f"{bucket['key_as_string']}: {bucket['doc_count']} books")
```

---

## 5. Nested Aggregations (Most Powerful Pattern)

Run a sub-aggregation inside a bucket aggregation — like GROUP BY with an inner COUNT/AVG:

```python
# Average rating per genre
response = es.search(
    index="books",
    aggs={
        "by_genre": {
            "terms": {
                "field": "genre",
                "size": 10
            },
            "aggs": {           # sub-aggregation
                "avg_rating": {
                    "avg": {"field": "rating"}
                },
                "top_rated": {
                    "top_hits": {
                        "size": 1,
                        "sort": [{"rating": {"order": "desc"}}],
                        "_source": ["title", "rating"]
                    }
                }
            }
        }
    },
    size=0
)

for bucket in response['aggregations']['by_genre']['buckets']:
    genre = bucket['key']
    count = bucket['doc_count']
    avg = bucket['avg_rating']['value']
    top = bucket['top_rated']['hits']['hits'][0]['_source']
    print(f"{genre}: {count} books, avg rating={avg:.2f}, top='{top['title']}'")
```

---

## 6. Aggregations + Search Combined

Search and aggregate at the same time — this is how faceted search UIs work:

```python
def faceted_search(query_text, genre_filter=None):
    """
    Returns search results AND facet counts simultaneously.
    """
    query = {"match_all": {}}
    filter_clauses = []

    if query_text:
        query = {"match": {"description": query_text}}

    if genre_filter:
        filter_clauses.append({"term": {"genre": genre_filter}})

    response = es.search(
        index="books",
        query={
            "bool": {
                "must": [query],
                "filter": filter_clauses
            }
        },
        aggs={
            "genres": {
                "terms": {"field": "genre", "size": 20}
            },
            "avg_rating": {
                "avg": {"field": "rating"}
            },
            "rating_histogram": {
                "histogram": {
                    "field": "rating",
                    "interval": 0.5
                }
            }
        },
        size=10
    )

    return {
        "total": response['hits']['total']['value'],
        "results": [h['_source'] for h in response['hits']['hits']],
        "facets": {
            "genres": response['aggregations']['genres']['buckets'],
            "avg_rating": response['aggregations']['avg_rating']['value'],
        }
    }

result = faceted_search("programming")
print(f"Found {result['total']} books")
print("Genre facets:", result['facets']['genres'])
```

---

## 7. Cardinality Aggregation (Count Unique Values)

```python
response = es.search(
    index="books",
    aggs={
        "unique_genres": {
            "cardinality": {"field": "genre"}   # approx unique count
        }
    },
    size=0
)
print(f"Unique genres: {response['aggregations']['unique_genres']['value']}")
```

---

## Aggregations vs SQL Reference

| SQL | Elasticsearch |
|-----|---------------|
| `GROUP BY field` | `terms` aggregation |
| `COUNT(*)` | `value_count` |
| `AVG(field)` | `avg` |
| `MAX(field)` | `max` |
| `MIN(field)` | `min` |
| `SUM(field)` | `sum` |
| `GROUP BY DATEPART(year, date)` | `date_histogram` |
| `BETWEEN x AND y` | `range` aggregation |
| `COUNT(DISTINCT field)` | `cardinality` |

---

## Reference Links

- [Aggregations overview](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html)
- [Terms aggregation](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html)
- [Date histogram](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-datehistogram-aggregation.html)

---

**← Previous:** [05 · Searching & Querying](./05_searching_and_querying.md)  
**Next →** [07 · RAG — PDFs & SQL to Elasticsearch](./07_rag_and_documents.md)
