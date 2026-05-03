# 09 · Tips, Patterns & Next Steps

> A quick reference of common patterns, mistakes to avoid, and where to go from here.

---

## Common Mistakes & How to Avoid Them

### 1. Using `term` on a `text` field

```python
# ❌ WRONG — text fields are analyzed (lowercased)
es.search(index="books", query={"term": {"title": "Python Crash Course"}})
# Returns nothing because "title" is analyzed, stored as tokens

# ✅ RIGHT — use match for text fields
es.search(index="books", query={"match": {"title": "Python Crash Course"}})

# ✅ OR — define a keyword sub-field in mapping
# "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
# Then:
es.search(index="books", query={"term": {"title.keyword": "Python Crash Course"}})
```

### 2. Forgetting to Refresh in Tests

```python
# After indexing, data takes ~1s to be searchable
es.index(index="books", document={...})
# Immediately searching may return 0 results!

# Fix: refresh explicitly (only in tests)
es.indices.refresh(index="books")
# Now search works
```

### 3. Changing Mappings After the Fact

Mappings are **immutable** for existing fields. You can add new fields, but you can't change a field from `text` to `keyword`.

```python
# If you need to change a mapping:
# 1. Create a new index with correct mapping
# 2. Reindex data from old to new
es.reindex(body={
    "source": {"index": "books_v1"},
    "dest": {"index": "books_v2"}
})
# 3. Create alias pointing to new index (zero downtime)
es.indices.put_alias(index="books_v2", name="books")
```

### 4. Not Using Bulk for Large Datasets

```python
# ❌ SLOW — individual requests
for doc in 10000_documents:
    es.index(index="books", document=doc)

# ✅ FAST — bulk API
helpers.bulk(es, actions)  # 10-100x faster
```

### 5. Using `from_` for Deep Pagination

```python
# ❌ Problematic for large offsets
es.search(index="books", from_=10000, size=10)  # gets slow and expensive

# ✅ Use search_after for deep pagination
response = es.search(
    index="books",
    sort=[{"_id": "asc"}],
    search_after=["last_id_from_previous_page"],
    size=10
)
```

---

## Useful Patterns

### Index Aliases (Zero-Downtime Reindexing)

```python
# Always write to an alias, not directly to index name
# This lets you swap indices without changing application code

# Create alias
es.indices.put_alias(index="books_v1", name="books")

# Later, reindex to v2 and swap alias atomically
es.indices.update_aliases(actions=[
    {"remove": {"index": "books_v1", "alias": "books"}},
    {"add":    {"index": "books_v2", "alias": "books"}}
])
# Your app code using "books" continues working with no downtime
```

### Index Templates (Apply Settings to Future Indices)

```python
# For time-series indices like logs-2024-01, logs-2024-02...
es.indices.put_index_template(
    name="logs_template",
    body={
        "index_patterns": ["logs-*"],
        "template": {
            "settings": {"number_of_shards": 1},
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"}
                }
            }
        }
    }
)
```

### Highlight Search Terms

```python
response = es.search(
    index="books",
    query={"match": {"description": "agile craftsmanship"}},
    highlight={
        "fields": {
            "description": {
                "fragment_size": 150,
                "number_of_fragments": 3,
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
    }
)

for hit in response['hits']['hits']:
    if 'highlight' in hit:
        print(hit['highlight']['description'])
# Output: "A handbook of <mark>agile</mark> software <mark>craftsmanship</mark>."
```

### Suggest / Autocomplete

```python
# Index setup — add completion field
mapping = {
    "mappings": {
        "properties": {
            "title": {"type": "text"},
            "title_suggest": {
                "type": "completion"   # special field for autocomplete
            }
        }
    }
}

# Index document with suggest field
es.index(
    index="books",
    document={
        "title": "Python Crash Course",
        "title_suggest": {
            "input": ["Python Crash Course", "Python", "Crash Course"]
        }
    }
)

# Query autocomplete
response = es.search(
    index="books",
    suggest={
        "title_autocomplete": {
            "prefix": "py",    # user typed "py"
            "completion": {
                "field": "title_suggest",
                "size": 5
            }
        }
    }
)

suggestions = response['suggest']['title_autocomplete'][0]['options']
for s in suggestions:
    print(s['text'])   # "Python Crash Course"
```

---

## Monitoring Your Cluster

```python
# Cluster health
health = es.cluster.health()
print(f"Status: {health['status']}")
print(f"Active shards: {health['active_shards']}")

# Index stats
stats = es.indices.stats(index="books")
docs = stats['indices']['books']['total']['docs']
print(f"Docs: {docs['count']}, Deleted: {docs['deleted']}")

# Node info
nodes = es.nodes.info()
for node_id, node in nodes['nodes'].items():
    print(f"Node: {node['name']}, OS: {node['os']['name']}")
```

---

## Performance Tips

| Tip | Why |
|-----|-----|
| Use `filter` inside `bool` for yes/no conditions | Filters are cached and don't compute scores |
| Set `_source=False` or list only needed fields | Reduces network payload |
| Use bulk API for indexing | 10-100x faster than individual requests |
| Set `size=0` when only aggregating | Skip fetching documents |
| Use `keyword` fields for grouping/sorting | `text` fields can't be sorted/aggregated directly |
| Use `number_of_replicas=0` in dev | Avoids "yellow" status on single node |
| Don't use dynamic mapping in production | Unexpected field types can cause issues |

---

## Where to Go From Here

After completing this handbook and project, you're ready for:

| Topic | What to Learn |
|-------|---------------|
| **Vector search at scale** | Elasticsearch ELSER, custom embedding models |
| **Kibana** | Visualize data, build dashboards |
| **Logstash / Beats** | Ingest data pipelines |
| **Index lifecycle management (ILM)** | Auto-delete old indices, move to cold storage |
| **Cross-cluster search** | Search across multiple ES clusters |
| **Security** | TLS, role-based access control, API keys |
| **Scaling** | Multi-node clusters, dedicated master/data nodes |

---

## Quick Reference Card

```python
# Connect
es = Elasticsearch("http://localhost:9200")

# Index operations
es.indices.create(index="name", body=mapping)
es.indices.exists(index="name")
es.indices.delete(index="name")
es.indices.refresh(index="name")

# Document CRUD
es.index(index="i", id="1", document={...})
es.get(index="i", id="1")
es.update(index="i", id="1", doc={...})
es.delete(index="i", id="1")
helpers.bulk(es, actions)

# Search
es.search(index="i", query={...}, size=10, from_=0)
es.count(index="i", query={...})

# Aggregations
es.search(index="i", aggs={...}, size=0)

# Cluster
es.cluster.health()
es.cat.indices(v=True)  # human-readable index listing
```

---

## Reference Links

- [Elasticsearch Python client](https://elasticsearch-py.readthedocs.io/)
- [Query DSL reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Mapping reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html)
- [kNN vector search](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)
- [Best practices](https://www.elastic.co/guide/en/elasticsearch/reference/current/best-practices.html)
- [Elastic community forum](https://discuss.elastic.co/)

---

**← Previous:** [08 · FastAPI Project](./08_fastapi_project.md)

---

*End of Elasticsearch Handbook — you now have everything to build search features and RAG pipelines in your projects.*
