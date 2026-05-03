# 04 · CRUD Operations with Python

> **Goal:** Create indices, index documents, retrieve, update, and delete them using the `elasticsearch-py` client.

---

## Setup

```python
from elasticsearch import Elasticsearch, helpers
import json

es = Elasticsearch("http://localhost:9200")
INDEX = "books"
```

---

## 1. Create an Index with Mapping

Always define your mapping upfront — it's hard to change later.

```python
def create_index():
    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0   # 0 = no replicas (fine for dev)
        },
        "mappings": {
            "properties": {
                "title":       { "type": "text" },
                "author":      { "type": "text" },
                "genre":       { "type": "keyword" },   # exact match
                "year":        { "type": "integer" },
                "rating":      { "type": "float" },
                "description": { "type": "text" },
                "tags":        { "type": "keyword" },
                "published_at":{ "type": "date", "format": "yyyy-MM-dd" }
            }
        }
    }

    # Only create if it doesn't exist
    if not es.indices.exists(index=INDEX):
        response = es.indices.create(index=INDEX, body=mapping)
        print(f"Index created: {response['acknowledged']}")
    else:
        print(f"Index '{INDEX}' already exists.")

create_index()
```

---

## 2. Index a Single Document (Create)

```python
def index_document(doc_id=None, document=None):
    """
    Index a document. If doc_id is None, ES auto-generates an ID.
    """
    doc = document or {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "genre": "Programming",
        "year": 2008,
        "rating": 4.5,
        "description": "A handbook of agile software craftsmanship.",
        "tags": ["software", "best-practices", "refactoring"],
        "published_at": "2008-08-01"
    }

    if doc_id:
        response = es.index(index=INDEX, id=doc_id, document=doc)
    else:
        response = es.index(index=INDEX, document=doc)

    print(f"Indexed document ID: {response['_id']}, Result: {response['result']}")
    return response['_id']

doc_id = index_document(doc_id="1")
```

---

## 3. Bulk Index Multiple Documents

For indexing many documents efficiently — always prefer bulk over individual requests.

```python
def bulk_index(documents):
    """
    Bulk index a list of documents.
    Each doc should have a '_id' key for custom IDs (optional).
    """
    actions = []
    for doc in documents:
        action = {
            "_index": INDEX,
            "_source": {k: v for k, v in doc.items() if k != "_id"}
        }
        if "_id" in doc:
            action["_id"] = doc["_id"]
        actions.append(action)

    success, failed = helpers.bulk(es, actions, raise_on_error=False)
    print(f"Bulk indexed: {success} success, {len(failed)} failed")
    return success, failed


books = [
    {
        "_id": "2",
        "title": "The Pragmatic Programmer",
        "author": "David Thomas, Andrew Hunt",
        "genre": "Programming",
        "year": 1999,
        "rating": 4.6,
        "description": "From journeyman to master programmer.",
        "tags": ["software", "productivity"],
        "published_at": "1999-10-20"
    },
    {
        "_id": "3",
        "title": "Deep Learning",
        "author": "Ian Goodfellow",
        "genre": "Machine Learning",
        "year": 2016,
        "rating": 4.4,
        "description": "The definitive textbook on deep learning.",
        "tags": ["AI", "neural-networks", "mathematics"],
        "published_at": "2016-11-18"
    },
    {
        "_id": "4",
        "title": "Python Crash Course",
        "author": "Eric Matthes",
        "genre": "Programming",
        "year": 2019,
        "rating": 4.7,
        "description": "A hands-on, project-based introduction to Python.",
        "tags": ["python", "beginner", "projects"],
        "published_at": "2019-05-03"
    },
]

bulk_index(books)
```

---

## 4. Read — Get a Document by ID

```python
def get_document(doc_id):
    try:
        response = es.get(index=INDEX, id=doc_id)
        print(f"Found document: {response['_source']['title']}")
        return response['_source']
    except Exception as e:
        print(f"Document not found: {e}")
        return None

doc = get_document("1")
print(doc)
```

---

## 5. Check If a Document Exists

```python
def document_exists(doc_id):
    exists = es.exists(index=INDEX, id=doc_id)
    print(f"Document {doc_id} exists: {exists}")
    return exists

document_exists("1")   # True
document_exists("99")  # False
```

---

## 6. Update a Document

### Partial Update (recommended)

```python
def update_document(doc_id, fields_to_update):
    """Update specific fields without replacing the entire document."""
    response = es.update(
        index=INDEX,
        id=doc_id,
        doc=fields_to_update
    )
    print(f"Updated document {doc_id}: {response['result']}")
    return response

update_document("1", {"rating": 4.8, "tags": ["software", "clean-code", "refactoring"]})
```

### Full Replace (use index() with same ID)

```python
def replace_document(doc_id, new_document):
    """Completely replace a document."""
    response = es.index(index=INDEX, id=doc_id, document=new_document)
    print(f"Replaced document {doc_id}: {response['result']}")
```

### Update by Script (for computed updates)

```python
def increment_field(doc_id, field, increment_by=1):
    """Increment a numeric field using a Painless script."""
    response = es.update(
        index=INDEX,
        id=doc_id,
        script={
            "source": f"ctx._source.{field} += params.amount",
            "params": {"amount": increment_by}
        }
    )
    print(f"Script update result: {response['result']}")
```

---

## 7. Delete a Document

```python
def delete_document(doc_id):
    try:
        response = es.delete(index=INDEX, id=doc_id)
        print(f"Deleted document {doc_id}: {response['result']}")
    except Exception as e:
        print(f"Error deleting document: {e}")

# delete_document("4")   # Uncomment to test
```

---

## 8. Delete an Index

```python
def delete_index(index_name):
    if es.indices.exists(index=index_name):
        response = es.indices.delete(index=index_name)
        print(f"Deleted index '{index_name}': {response['acknowledged']}")
    else:
        print(f"Index '{index_name}' does not exist.")

# delete_index(INDEX)   # Uncomment to test
```

---

## 9. Refresh Index (Force Near-Real-Time)

After indexing, ES takes ~1 second to make data searchable. In tests, force a refresh:

```python
# Force index to be searchable immediately (only for testing!)
es.indices.refresh(index=INDEX)
```

---

## 10. Get Index Info

```python
# View mapping
mapping = es.indices.get_mapping(index=INDEX)
print(json.dumps(dict(mapping), indent=2))

# View settings
settings = es.indices.get_settings(index=INDEX)
print(json.dumps(dict(settings), indent=2))

# Count documents in index
count = es.count(index=INDEX)
print(f"Total documents: {count['count']}")
```

---

## CRUD at a Glance

```python
# CREATE
es.index(index="books", id="1", document={...})

# READ
es.get(index="books", id="1")

# UPDATE (partial)
es.update(index="books", id="1", doc={"rating": 4.9})

# DELETE
es.delete(index="books", id="1")

# BULK
helpers.bulk(es, actions)
```

---

## Reference Links

- [Python client — index API](https://elasticsearch-py.readthedocs.io/en/v8.13.0/api/elasticsearch.html#elasticsearch.Elasticsearch.index)
- [Bulk helpers](https://elasticsearch-py.readthedocs.io/en/v8.13.0/helpers.html)
- [Update API](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update.html)

---

**← Previous:** [03 · Installation](./03_installation_ubuntu.md)  
**Next →** [05 · Searching & Querying](./05_searching_and_querying.md)
