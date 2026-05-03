from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import Elasticsearch
from app.models import ProductSearchRequest, ProductSearchResponse
from app.services import es_service
from app.config import get_settings

router = APIRouter(prefix="/api/products", tags=["Products"])
settings = get_settings()


def get_es() -> Elasticsearch:
    return es_service.get_es_client()


@router.post("/search", response_model=ProductSearchResponse)
def search_products(request: ProductSearchRequest, es: Elasticsearch = Depends(get_es)):
    """
    Search products with full-text search, filters, and facets.

    - **query**: Full-text search across name, description, tags, brand
    - **category**: Exact filter by category (e.g., "Electronics")
    - **brand**: Exact filter by brand
    - **min_price / max_price**: Price range filter
    - **min_rating**: Minimum rating filter
    - **sort_by**: relevance | price | rating
    - **page / page_size**: Pagination
    """
    try:
        result = es_service.search_products(
            es=es,
            query=request.query,
            category=request.category,
            brand=request.brand,
            min_price=request.min_price,
            max_price=request.max_price,
            min_rating=request.min_rating,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}")
def get_product(product_id: str, es: Elasticsearch = Depends(get_es)):
    """Get a single product by its Elasticsearch ID."""
    product = es_service.get_product_by_id(es, product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")
    return product


@router.post("/index/bulk")
def bulk_index_products(products: list[dict], es: Elasticsearch = Depends(get_es)):
    """
    Bulk index a list of products.

    Each product object should have: name, description, price, category,
    brand, rating, stock. Optionally include 'id' to set a custom ES document ID.
    """
    if not products:
        raise HTTPException(status_code=400, detail="Products list cannot be empty")

    success, failed = es_service.index_products(es, products)
    return {
        "indexed": success,
        "failed": failed,
        "message": f"Successfully indexed {success} products"
    }
