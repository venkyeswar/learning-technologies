from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import products, rag
from app.services.es_service import get_es_client, setup_indices
from app.models import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup Elasticsearch indices on startup."""
    print("🚀 Starting up — connecting to Elasticsearch...")
    try:
        es = get_es_client()
        if es.ping():
            print("✅ Elasticsearch connected.")
            setup_indices(es)
        else:
            print("⚠️  Elasticsearch not reachable — some endpoints may fail.")
    except Exception as e:
        print(f"⚠️  Startup warning: {e}")
    yield
    print("🛑 Shutting down.")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="""
## Elasticsearch Handbook — API

A demonstration API showing:
- **Product Search** — full-text search, filters, facets, pagination
- **RAG** — PDF ingestion, chunking, embeddings, hybrid search

### Quick Start
1. Start Elasticsearch: `docker compose up -d`
2. Run the API: `uvicorn app.main:app --reload`
3. Seed data: `python scripts/seed_products.py`
4. Open `/docs` for interactive API docs
    """,
    lifespan=lifespan
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(products.router)
app.include_router(rag.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Elasticsearch Handbook API",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health():
    """Check API and Elasticsearch health."""
    try:
        es = get_es_client()
        info = es.info()
        cluster_health = es.cluster.health()
        indices = list(es.indices.get_alias(index="*").keys())
        indices = [i for i in indices if not i.startswith(".")]  # hide system indices

        return HealthResponse(
            status="ok",
            elasticsearch=cluster_health["status"],
            cluster_name=info["cluster_name"],
            indices=indices
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            elasticsearch="unreachable",
            indices=[]
        )
