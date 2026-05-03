# 08 · FastAPI Project — Product Search + RAG API

> **Goal:** Build a production-ready FastAPI application that demonstrates both e-commerce product search and document RAG using Elasticsearch.

---

## What You'll Build

```
┌─────────────────────────────────────────────────────────┐
│               FastAPI Application                        │
│                                                         │
│  POST /api/products/search     → product search         │
│  GET  /api/products/{id}       → get product by ID      │
│  POST /api/products/index      → index products         │
│  POST /api/rag/ingest-pdf      → upload & chunk PDF     │
│  POST /api/rag/query           → RAG question answering │
│  GET  /api/health              → health check           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
         Elasticsearch :9200
         ┌──────────────────┐
         │ Index: products  │
         │ Index: doc_chunks│
         └──────────────────┘
```

---

## Project Structure

```
elasticsearch-project/
├── app/
│   ├── main.py              ← FastAPI app entry point
│   ├── config.py            ← Settings & ES connection
│   ├── models.py            ← Pydantic models
│   ├── routers/
│   │   ├── products.py      ← Product search endpoints
│   │   └── rag.py           ← RAG endpoints
│   └── services/
│       ├── es_service.py    ← Elasticsearch operations
│       └── rag_service.py   ← PDF chunking + search
├── scripts/
│   ├── seed_products.py     ← Load sample data
│   └── ingest_pdf.py        ← CLI tool for PDF ingestion
├── .env
├── requirements.txt
└── docker-compose.yml
```

---

## See the Full Project

The complete working project with all files is in:  
**`../project/`** — relative to this docs folder.

See [Project README](../project/README.md) for setup and running instructions.

---

## API Endpoints Summary

### Product Search

```
POST /api/products/search
{
  "query": "wireless headphones",
  "category": "Electronics",        ← optional filter
  "min_price": 5000,                 ← optional filter
  "max_price": 25000,                ← optional filter
  "min_rating": 4.0,                 ← optional filter
  "page": 1,
  "page_size": 10,
  "sort_by": "rating",               ← price | rating | relevance
  "sort_order": "desc"
}

Response:
{
  "total": 42,
  "page": 1,
  "results": [...],
  "facets": {
    "categories": [{"key": "Electronics", "count": 42}],
    "brands": [...]
  }
}
```

### RAG Query

```
POST /api/rag/query
{
  "question": "What are the key concepts in machine learning?",
  "source_filter": "ml_guide",       ← optional, filter by document
  "top_k": 5                         ← number of chunks to retrieve
}

Response:
{
  "answer": "Based on the documents...",
  "sources": [
    {"content": "...", "source": "ml_guide.pdf", "page": 3, "score": 0.92}
  ]
}
```

---

**Next:** Read the project files in `../project/` for complete implementation.
