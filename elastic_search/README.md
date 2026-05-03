# Elasticsearch Handbook

Your hands-on handbook for learning Elasticsearch — from zero to building RAG pipelines and search APIs.

---

## Who This Is For

You've heard of Elasticsearch, you want to use it in your Python/FastAPI projects for **search** and **RAG (AI document Q&A)** — and you want to learn it clean, not get lost in enterprise features you don't need yet.

---

## What You'll Learn

By the end of this handbook + project, you will be able to:

- ✅ Understand what Elasticsearch is and when to use it
- ✅ Install and run it locally (Docker or Ubuntu)
- ✅ Create indices with proper mappings
- ✅ Index, retrieve, update, and delete documents
- ✅ Write full-text search queries with filters and fuzzy matching
- ✅ Use aggregations for analytics and faceted search UIs
- ✅ Convert PDFs and SQL databases into searchable ES documents
- ✅ Build a semantic/hybrid search pipeline for RAG
- ✅ Expose all of this through a clean FastAPI API

---

## Docs — Read in Order

| # | File | What You Learn |
|---|------|----------------|
| 01 | [What is Elasticsearch?](docs/01_what_is_elasticsearch.md) | Overview, use cases, mental model |
| 02 | [Core Concepts](docs/02_core_concepts.md) | Cluster, Index, Document, Mapping, Analyzers, Scoring |
| 03 | [Installation (Ubuntu + Docker)](docs/03_installation_ubuntu.md) | Get ES running, Python client setup |
| 04 | [CRUD Operations](docs/04_crud_operations.md) | Create, read, update, delete, bulk indexing |
| 05 | [Searching & Querying](docs/05_searching_and_querying.md) | match, bool, term, range, fuzzy, pagination |
| 06 | [Aggregations](docs/06_aggregations.md) | Group by, stats, histograms, faceted search |
| 07 | [RAG — PDFs & SQL to ES](docs/07_rag_and_documents.md) | Chunking, embeddings, semantic/hybrid search |
| 08 | [FastAPI Project](docs/08_fastapi_project.md) | Project overview and API design |
| 09 | [Tips & Next Steps](docs/09_tips_and_next_steps.md) | Common mistakes, patterns, what to learn next |

---

## Project

The `project/` folder contains a complete, working FastAPI application.

**See [project/README.md](project/README.md) for setup instructions.**

```
Quick start:
  cd project
  docker compose up -d
  pip install -r requirements.txt
  python scripts/seed_products.py
  uvicorn app.main:app --reload
  open http://localhost:8000/docs
```

---

## Reference Links

- [Elasticsearch Docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Python Client](https://elasticsearch-py.readthedocs.io/)
- [Kibana](https://www.elastic.co/guide/en/kibana/current/)
- [sentence-transformers](https://www.sbert.net/)
