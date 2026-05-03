# Elasticsearch Handbook — Project

A working FastAPI application demonstrating:
- **Product Search** — full-text, filters, facets, pagination
- **RAG Pipeline** — PDF ingestion, chunking, embeddings, hybrid search

---

## Quick Start

### 1. Start Elasticsearch

```bash
docker compose up -d
# Wait ~30 seconds for ES to be ready
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Seed Sample Data

```bash
python scripts/seed_products.py
```

### 4. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** — interactive Swagger UI.

---

## API Endpoints

### Health
```
GET  /api/health              → Check ES connection and status
```

### Products
```
POST /api/products/search     → Search products
GET  /api/products/{id}       → Get product by ID
POST /api/products/index/bulk → Bulk index products
```

### RAG
```
POST /api/rag/ingest-pdf      → Upload and index a PDF
POST /api/rag/query           → Ask a question against indexed docs
GET  /api/rag/sources         → List all ingested documents
```

---

## Example Requests

### Search for wireless headphones under ₹25,000

```python
import httpx

response = httpx.post("http://localhost:8000/api/products/search", json={
    "query": "wireless headphones noise cancelling",
    "category": "Electronics",
    "max_price": 25000,
    "min_rating": 4.0,
    "sort_by": "rating",
    "page": 1,
    "page_size": 5
})
print(response.json())
```

### Ingest a PDF for RAG

```python
import httpx

with open("my_document.pdf", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/rag/ingest-pdf",
        files={"file": ("my_document.pdf", f, "application/pdf")},
        params={"chunk_size": 500, "overlap": 50}
    )
print(response.json())
```

### Query ingested documents

```python
response = httpx.post("http://localhost:8000/api/rag/query", json={
    "question": "What are the key concepts explained in this document?",
    "top_k": 5,
    "search_type": "hybrid"
})
data = response.json()
print("Answer:", data["answer"])
for source in data["sources"]:
    print(f"  [{source['source']} p.{source['page']}] score={source['score']:.3f}")
```

---

## Project Structure

```
project/
├── app/
│   ├── main.py              ← FastAPI app, startup, CORS
│   ├── config.py            ← Settings from .env
│   ├── models.py            ← Pydantic request/response models
│   ├── routers/
│   │   ├── products.py      ← Product search endpoints
│   │   └── rag.py           ← PDF ingest + RAG query endpoints
│   └── services/
│       ├── es_service.py    ← All Elasticsearch operations
│       └── rag_service.py   ← PDF chunking + embedding logic
├── scripts/
│   ├── seed_products.py     ← Load 20 sample products
│   └── ingest_pdf.py        ← CLI: ingest any PDF
├── .env                     ← Configuration
├── requirements.txt
└── docker-compose.yml       ← Elasticsearch + Kibana
```

---

## Integrating a Real LLM

In `app/services/rag_service.py`, find the `build_rag_answer()` function and replace the placeholder with your LLM call:

```python
# Claude (Anthropic)
import anthropic
client = anthropic.Anthropic(api_key="your-key")
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)
return message.content[0].text
```

---

## Kibana UI

With docker compose running, open **http://localhost:5601**.

Navigate to: **Dev Tools** → Run queries against your indices interactively.
