from pydantic import BaseModel, Field
from typing import Optional, List, Any


# ─── Product Models ──────────────────────────────────────────────────────────

class Product(BaseModel):
    name: str
    description: str
    price: float
    category: str
    brand: str
    rating: float = Field(ge=0, le=5)
    stock: int = Field(ge=0)
    tags: List[str] = []
    image_url: Optional[str] = None


class ProductSearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: str = Field(default="relevance")  # relevance | price | rating
    sort_order: str = Field(default="desc")    # asc | desc


class FacetBucket(BaseModel):
    key: str
    count: int


class ProductSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    results: List[dict]
    facets: dict


# ─── RAG Models ──────────────────────────────────────────────────────────────

class RAGQueryRequest(BaseModel):
    question: str
    source_filter: Optional[str] = None   # filter by document name
    top_k: int = Field(default=5, ge=1, le=20)
    search_type: str = Field(default="hybrid")  # hybrid | semantic | keyword


class SourceChunk(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    score: float


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]
    search_type: str


class IngestResponse(BaseModel):
    filename: str
    chunks_created: int
    message: str


# ─── General ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    elasticsearch: str
    cluster_name: Optional[str] = None
    indices: List[str] = []
