# 05 · Searching & Querying

> **Goal:** Master the Query DSL — match, term, bool, range, fuzzy, and multi-field queries. Everything you need for real search features.

---

## The Query Structure

Every search in Elasticsearch follows this pattern:

```python
response = es.search(
    index="books",
    query={...},        # What to find
    size=10,            # How many results (default: 10)
    from_=0,            # Offset for pagination
    sort=[...],         # How to sort (optional)
    _source=["title"],  # Which fields to return (optional)
)

# Access results
hits = response['hits']['hits']
total = response['hits']['total']['value']

for hit in hits:
    print(hit['_score'], hit['_source'])
```

---

## Query Types Overview

```
Queries (affect _score)          Filters (yes/no, cached)
─────────────────────────        ──────────────────────────
match                            term
match_phrase                     terms
multi_match                      range
fuzzy                            exists
query_string                     bool → filter clause
```

> **Rule:** Use **queries** when relevance matters (full-text search). Use **filters** inside `bool.filter` when it's a yes/no decision (status = "active"). Filters are faster and cached.

---

## 1. Match Query (Full-Text Search)

The most common query. Analyzes the search text and finds matching documents.

```python
# Basic match
response = es.search(
    index="books",
    query={
        "match": {
            "description": "agile software craftsmanship"
        }
    }
)

# Match with options
response = es.search(
    index="books",
    query={
        "match": {
            "description": {
                "query": "agile software",
                "operator": "and"    # Both words must appear (default: "or")
            }
        }
    }
)
```

---

## 2. Match Phrase Query

Requires words to appear **in order**, adjacent to each other.

```python
response = es.search(
    index="books",
    query={
        "match_phrase": {
            "description": "deep learning"
        }
    }
)
# Matches "deep learning techniques" but not "learning deep things"
```

---

## 3. Multi-Match Query

Search across **multiple fields** at once.

```python
response = es.search(
    index="books",
    query={
        "multi_match": {
            "query": "python programming",
            "fields": ["title", "description", "tags"],
            # Boost title matches 2x
            # "fields": ["title^2", "description", "tags"],
            "type": "best_fields"   # score based on best matching field
        }
    }
)
```

Multi-match types:
- `best_fields` — score from the best matching field (default)
- `most_fields` — combine scores from all matching fields
- `cross_fields` — treat all fields as one big field

---

## 4. Term Query (Exact Match)

For `keyword` fields — exact value, no analysis.

```python
# Exact match on keyword field
response = es.search(
    index="books",
    query={
        "term": {
            "genre": "Programming"   # Must match exactly (case-sensitive)
        }
    }
)
```

> ⚠️ Never use `term` on a `text` field — it won't work as expected because text fields are analyzed (lowercased, tokenized).

---

## 5. Terms Query (Match Any of Multiple Values)

```python
response = es.search(
    index="books",
    query={
        "terms": {
            "genre": ["Programming", "Machine Learning"]
        }
    }
)
```

---

## 6. Range Query

```python
# Books from 2015 onwards with rating >= 4.5
response = es.search(
    index="books",
    query={
        "range": {
            "year": {
                "gte": 2015,   # greater than or equal
                "lte": 2023    # less than or equal
            }
        }
    }
)

# Also: gt (greater than), lt (less than)
# For dates:
response = es.search(
    index="books",
    query={
        "range": {
            "published_at": {
                "gte": "2010-01-01",
                "lte": "2020-12-31",
                "format": "yyyy-MM-dd"
            }
        }
    }
)
```

---

## 7. Bool Query — The Most Important Query

Combine multiple queries with logical operators:

```python
response = es.search(
    index="books",
    query={
        "bool": {
            "must":     [...],   # AND — must match, contributes to score
            "should":   [...],   # OR — nice to match, boosts score
            "must_not": [...],   # NOT — must not match, no score
            "filter":   [...]    # AND — must match, does NOT affect score (faster)
        }
    }
)
```

### Real Example — E-commerce Style Search

```python
def search_books(query_text, genre=None, min_rating=None, min_year=None):
    """
    Full search: text search + filters combined.
    """
    must_clauses = []
    filter_clauses = []
    should_clauses = []

    # Full-text search (affects score)
    if query_text:
        must_clauses.append({
            "multi_match": {
                "query": query_text,
                "fields": ["title^3", "author^2", "description", "tags"]
            }
        })

    # Exact filter (doesn't affect score, but faster)
    if genre:
        filter_clauses.append({
            "term": {"genre": genre}
        })

    if min_rating:
        filter_clauses.append({
            "range": {"rating": {"gte": min_rating}}
        })

    if min_year:
        filter_clauses.append({
            "range": {"year": {"gte": min_year}}
        })

    query = {
        "bool": {
            "must": must_clauses if must_clauses else [{"match_all": {}}],
            "filter": filter_clauses,
            "should": should_clauses
        }
    }

    response = es.search(
        index="books",
        query=query,
        size=10,
        from_=0
    )

    results = []
    for hit in response['hits']['hits']:
        results.append({
            "id": hit['_id'],
            "score": hit['_score'],
            **hit['_source']
        })

    return {
        "total": response['hits']['total']['value'],
        "results": results
    }

# Usage
print(search_books("python programming", genre="Programming"))
print(search_books("machine learning", min_rating=4.0, min_year=2015))
```

---

## 8. Fuzzy Query (Typo Tolerance)

Matches documents even with spelling mistakes.

```python
response = es.search(
    index="books",
    query={
        "fuzzy": {
            "title": {
                "value": "pythn",      # typo: "pythn" instead of "python"
                "fuzziness": "AUTO",   # AUTO: 0 for 1-2 chars, 1 for 3-5, 2 for 6+
            }
        }
    }
)
```

Better approach — use `match` with fuzziness:

```python
response = es.search(
    index="books",
    query={
        "match": {
            "title": {
                "query": "pythn crash corse",  # two typos
                "fuzziness": "AUTO"
            }
        }
    }
)
```

---

## 9. Match All & Match None

```python
# Return ALL documents (sorted by _score desc)
response = es.search(index="books", query={"match_all": {}})

# Return NO documents
response = es.search(index="books", query={"match_none": {}})
```

---

## 10. Wildcard & Prefix Queries

```python
# Prefix: for autocomplete
response = es.search(
    index="books",
    query={"prefix": {"title": "py"}}   # matches "python", "pytest", etc.
)

# Wildcard: use sparingly, can be slow
response = es.search(
    index="books",
    query={"wildcard": {"title": "py*on"}}  # matches "python"
)
```

---

## 11. Sorting

```python
response = es.search(
    index="books",
    query={"match_all": {}},
    sort=[
        {"rating": {"order": "desc"}},   # sort by rating descending
        {"year": {"order": "asc"}},       # then by year ascending
        "_score"                          # finally by relevance
    ]
)
```

---

## 12. Pagination

```python
def paginate_search(query_text, page=1, page_size=10):
    offset = (page - 1) * page_size

    response = es.search(
        index="books",
        query={"match": {"description": query_text}},
        size=page_size,
        from_=offset
    )

    total = response['hits']['total']['value']
    total_pages = (total + page_size - 1) // page_size
    results = [hit['_source'] for hit in response['hits']['hits']]

    return {
        "page": page,
        "total_pages": total_pages,
        "total_results": total,
        "results": results
    }
```

> ⚠️ `from_` + `size` can't exceed 10,000 by default. For deep pagination, use [Search After](https://www.elastic.co/guide/en/elasticsearch/reference/current/paginate-search-results.html#search-after).

---

## 13. Source Filtering

Return only the fields you need — reduces network overhead.

```python
response = es.search(
    index="books",
    query={"match_all": {}},
    _source=["title", "author", "rating"],   # Only these fields
    size=5
)

# Exclude specific fields
response = es.search(
    index="books",
    query={"match_all": {}},
    _source={"excludes": ["description"]}
)
```

---

## Query Cheat Sheet

```python
# Match (full-text)
{"match": {"field": "search text"}}

# Exact match
{"term": {"field": "exact_value"}}

# Multiple exact values
{"terms": {"field": ["val1", "val2"]}}

# Number/date range
{"range": {"field": {"gte": 10, "lte": 100}}}

# Fuzzy (typo-tolerant)
{"match": {"field": {"query": "text", "fuzziness": "AUTO"}}}

# Multi-field search
{"multi_match": {"query": "text", "fields": ["f1", "f2"]}}

# Combine everything
{"bool": {"must": [...], "filter": [...], "should": [...], "must_not": [...]}}
```

---

## Reference Links

- [Query DSL overview](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Bool query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
- [Full-text queries](https://www.elastic.co/guide/en/elasticsearch/reference/current/full-text-queries.html)

---

**← Previous:** [04 · CRUD Operations](./04_crud_operations.md)  
**Next →** [06 · Aggregations & Analytics](./06_aggregations.md)
