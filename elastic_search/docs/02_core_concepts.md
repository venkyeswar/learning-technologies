# 02 · Core Concepts

> **Goal:** Learn the vocabulary of Elasticsearch — Cluster, Node, Index, Document, Shard, Mapping — before touching any code.

---

## The Big Picture

```
┌──────────────────────── CLUSTER ─────────────────────────┐
│                                                          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │   NODE 1    │    │   NODE 2    │    │   NODE 3    │  │
│   │  (master)   │    │  (data)     │    │  (data)     │  │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│          │                  │                  │         │
│   ┌──────▼──────────────────▼──────────────────▼──────┐  │
│   │                    INDEX: "products"              │  │
│   │   Shard 0 (primary)    │   Shard 1 (primary)      │  │
│   │   Shard 0 (replica)    │   Shard 1 (replica)      │  │
│   └───────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 1. Cluster

A **cluster** is a collection of one or more nodes (servers) that together hold all your data. Every cluster has a unique name (default: `elasticsearch`).

- For development: 1 node = 1 cluster is fine
- For production: 3+ nodes recommended for high availability

---

## 2. Node

A **node** is a single running instance of Elasticsearch. Each node has a role:

| Role | Responsibility |
|------|---------------|
| Master | Manages cluster state, index creation/deletion |
| Data | Stores data and handles search/indexing |
| Ingest | Pre-processes documents before indexing |
| Coordinating | Routes requests, merges results |

> In dev mode (single node), one node handles all roles.

---

## 3. Index

An **index** is like a database table — it's a collection of JSON documents that share a similar structure.

```
Index: "movies"
├── Document 1: { "title": "Inception", "year": 2010, "genre": "Sci-Fi" }
├── Document 2: { "title": "Interstellar", "year": 2014, "genre": "Sci-Fi" }
└── Document 3: { "title": "The Dark Knight", "year": 2008, "genre": "Action" }
```

Naming rules: lowercase, no spaces, no `*`, no `,`.

---

## 4. Document

A **document** is a single JSON record — the basic unit of data in Elasticsearch.

```json
{
  "_index": "movies",
  "_id": "1",
  "_source": {
    "title": "Inception",
    "director": "Christopher Nolan",
    "year": 2010,
    "rating": 8.8,
    "genre": ["Sci-Fi", "Thriller"],
    "synopsis": "A thief who steals corporate secrets through dream-sharing technology..."
  }
}
```

Key metadata fields:
- `_index` — which index the doc belongs to
- `_id` — unique identifier (auto-generated if not provided)
- `_source` — the actual JSON you stored
- `_score` — relevance score (appears in search results)

---

## 5. Shards

An index is split into **shards** — smaller pieces distributed across nodes. This is what makes Elasticsearch scalable.

```
Index "products" (10 million docs)
├── Shard 0  → Node 1  (2.5M docs)
├── Shard 1  → Node 2  (2.5M docs)
├── Shard 2  → Node 3  (2.5M docs)
└── Shard 3  → Node 1  (2.5M docs)
```

**Primary vs Replica shards:**
- **Primary** — the original shard
- **Replica** — a copy of a primary (for redundancy + read performance)

> For learning/dev: Don't worry about shard configuration. Defaults work fine.

---

## 6. Mapping

**Mapping** defines the schema of your index — what fields exist and what data type each field is. Similar to a CREATE TABLE in SQL.

```json
{
  "mappings": {
    "properties": {
      "title":     { "type": "text" },
      "year":      { "type": "integer" },
      "rating":    { "type": "float" },
      "genre":     { "type": "keyword" },
      "synopsis":  { "type": "text" },
      "created_at":{ "type": "date" }
    }
  }
}
```

### Important: `text` vs `keyword`

This is the most important mapping distinction for beginners:

| Type | Use for | Searchable how? | Example |
|------|---------|-----------------|---------|
| `text` | Full sentences, paragraphs | Analyzed (tokenized, lowercased) | `"The quick brown fox"` |
| `keyword` | IDs, tags, exact values | Exact match only | `"sci-fi"`, `"active"` |

```
"text" field: "Hello World"
→ Analyzer breaks it into tokens: ["hello", "world"]
→ You can search for "hello" and find it ✓

"keyword" field: "Hello World"
→ Stored as-is: "Hello World"
→ Search "hello" → No match ✗
→ Search "Hello World" → Match ✓
```

---

## 7. Inverted Index (How Search Actually Works)

When you index a `text` field, Elasticsearch builds an **inverted index** — a reverse lookup from word → document IDs:

```
Your documents:
  Doc 1: "Elasticsearch is fast"
  Doc 2: "Elasticsearch is scalable"
  Doc 3: "Python is fast and easy"

Inverted Index:
  "elasticsearch" → [Doc 1, Doc 2]
  "fast"          → [Doc 1, Doc 3]
  "is"            → [Doc 1, Doc 2, Doc 3]
  "scalable"      → [Doc 2]
  "python"        → [Doc 3]

Search "elasticsearch fast":
  → union/intersection of [Doc 1, Doc 2] and [Doc 1, Doc 3]
  → Doc 1 scores highest (appears in both!)
```

---

## 8. Analyzers

An **analyzer** controls how text is processed before indexing. The default (`standard`) analyzer:

1. **Tokenizes** — splits on whitespace and punctuation
2. **Lowercases** — `"Hello"` → `"hello"`
3. **Removes stop words** (optionally)

```
Input:  "Running Fast in New York!"
Tokens: ["running", "fast", "in", "new", "york"]
```

Common analyzers:
- `standard` — default, works for most English text
- `english` — also stems words (`"running"` → `"run"`)
- `simple` — splits on non-letters only
- Custom analyzers — you build your own

---

## 9. Relevance Score (`_score`)

When you search, every matching document gets a `_score`. Higher score = more relevant. By default, Elasticsearch uses the **BM25** algorithm (an improved TF-IDF):

- **Term Frequency (TF):** The more times a search term appears in a doc, the higher the score
- **Inverse Document Frequency (IDF):** Rare terms matter more than common ones
- **Field length:** A match in a short title scores higher than in a long body

---

## Quick Recap

```
Cluster
  └── Nodes (servers)
        └── Indices (like tables)
              └── Documents (JSON records)
                    └── Fields with Mappings (types)
                          └── Analyzed by Analyzers
                                └── Stored in Inverted Index
                                      └── Searched & Scored
```

---

## Reference Links

- [Mapping types](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html)
- [Inverted index explained](https://www.elastic.co/guide/en/elasticsearch/guide/current/inverted-index.html)
- [Analyzers](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-analyzers.html)
- [BM25 scoring](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-similarity.html)

---

**← Previous:** [01 · What is Elasticsearch?](./01_what_is_elasticsearch.md)  
**Next →** [03 · Installation on Ubuntu](./03_installation_ubuntu.md)
