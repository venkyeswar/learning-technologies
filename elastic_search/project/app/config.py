from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    elasticsearch_url: str = "http://localhost:9200"
    products_index: str = "products"
    chunks_index: str = "document_chunks"
    embedding_model: str = "all-MiniLM-L6-v2"
    app_title: str = "Elasticsearch Handbook API"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
