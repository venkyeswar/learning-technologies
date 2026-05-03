# 01 · What is Elasticsearch?

> **Goal:** Understand what Elasticsearch is, why it exists, and where it fits in modern software — in plain language.

---

## The Problem It Solves

Imagine you have a PostgreSQL database with 5 million product records. A user types `"red nike running shoes size 10"` in a search bar. A normal SQL `LIKE '%red nike running shoes%'` query:

- Scans every row (slow)
- Misses typos (`"nkie"` won't match `"nike"`)
- Can't rank results by relevance
- Can't handle synonyms (`"sneakers"` ≠ `"shoes"` in SQL)

**Elasticsearch solves all of this.**

---

## What Is Elasticsearch?

Elasticsearch is a **distributed search and analytics engine** built on top of [Apache Lucene](https://lucene.apache.org/). You store data in it as JSON documents, and it lets you search, filter, aggregate, and analyse that data at scale — in milliseconds.

```
┌─────────────────────────────────────────────────────┐
│                  Elasticsearch                      │
│                                                     │
│   Store JSON  →  Index it  →  Search it fast        │
│                                                     │
│   Full-text  |  Fuzzy  |  Filters  |  Aggregations  │
└─────────────────────────────────────────────────────┘
```

Key facts:
- Written in **Java**, but you interact with it over a simple **REST API** (JSON in, JSON out)
- Horizontally scalable — add more nodes when you need more power
- **Near real-time** — data is searchable within ~1 second of being indexed
- Open-source (Elastic License v2 / SSPL)

---

## Where Is It Used?

| Use Case | Example |
|----------|---------|
| **E-commerce search** | "Find all blue Adidas shoes under ₹5000" |
| **Log & metric analysis** | ELK Stack — Kibana dashboards over server logs |
| **RAG (AI / LLM)** | Store document chunks + embeddings, retrieve relevant context |
| **Autocomplete** | Suggest as the user types |
| **Geo search** | "Restaurants within 5 km of me" |
| **Security / SIEM** | Detect anomalies in millions of events per second |

---

## The ELK / Elastic Stack

You'll often hear about the **Elastic Stack**:

```
Beats / Logstash  →  Elasticsearch  →  Kibana
  (ingest data)       (store & search)   (visualize)
```

For this handbook we focus only on **Elasticsearch itself** — using Python to talk to it directly.

---

## How It Differs from a Regular Database

| Feature | PostgreSQL / MySQL | Elasticsearch |
|---|---|---|
| Data format | Tables & rows | JSON documents |
| Primary purpose | Transactional storage | Search & analytics |
| Query language | SQL | Query DSL (JSON) |
| Full-text search | Limited (`LIKE`, `tsvector`) | First-class citizen |
| Ranking / scoring | No | Yes (BM25 + custom) |
| Scalability | Vertical (mostly) | Horizontal (shards) |
| Fuzzy matching | No | Yes |

> **Rule of thumb:** Use a relational DB as your source of truth. Sync data into Elasticsearch for search and analytics.

---

## Core Mental Model

Think of Elasticsearch like a very smart library:

```
Library Analogy         →    Elasticsearch
─────────────────────────────────────────────
Library                 →    Cluster
Section (Fiction, Sci)  →    Index
A single book           →    Document (JSON)
Book's table of contents→    Inverted Index (how ES searches)
Librarian               →    Elasticsearch engine
```

The **inverted index** is the secret sauce — instead of scanning every document, ES pre-builds a map of `word → [list of documents containing it]`, making search lightning fast.

---

## Reference Links

- [Official Elasticsearch Docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [What is Elasticsearch? (Elastic.co)](https://www.elastic.co/what-is/elasticsearch)
- [Elasticsearch: The Definitive Guide (free online)](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html)

---

**Next →** [02 · Core Concepts](./02_core_concepts.md)
