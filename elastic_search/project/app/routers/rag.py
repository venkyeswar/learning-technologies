from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from elasticsearch import Elasticsearch
from app.models import RAGQueryRequest, RAGQueryResponse, IngestResponse, SourceChunk
from app.services import es_service, rag_service
from app.config import get_settings

router = APIRouter(prefix="/api/rag", tags=["RAG"])
settings = get_settings()


def get_es() -> Elasticsearch:
    return es_service.get_es_client()


@router.post("/ingest-pdf", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    chunk_size: int = 500,
    overlap: int = 50,
    es: Elasticsearch = Depends(get_es)
):
    """
    Upload a PDF and index it as searchable chunks.

    - Extracts text from each page
    - Splits into overlapping chunks
    - Generates semantic embeddings for each chunk
    - Stores in Elasticsearch for hybrid search
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        file_bytes = await file.read()

        # Step 1: Extract and chunk
        chunks = rag_service.pdf_bytes_to_chunks(
            file_bytes=file_bytes,
            filename=file.filename,
            chunk_size=chunk_size,
            overlap=overlap
        )

        if not chunks:
            raise HTTPException(status_code=400, detail="No text could be extracted from this PDF")

        # Step 2: Generate embeddings
        chunks_with_embeddings = rag_service.add_embeddings_to_chunks(chunks)

        # Step 3: Index into Elasticsearch
        success, failed = es_service.index_chunks(es, chunks_with_embeddings)

        return IngestResponse(
            filename=file.filename,
            chunks_created=success,
            message=f"Successfully ingested '{file.filename}' into {success} searchable chunks"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.post("/query", response_model=RAGQueryResponse)
def query_documents(request: RAGQueryRequest, es: Elasticsearch = Depends(get_es)):
    """
    Ask a question and retrieve relevant document chunks.

    - **question**: Your question in natural language
    - **source_filter**: Optional — only search within a specific document
    - **top_k**: Number of chunks to retrieve (1-20)
    - **search_type**: hybrid (recommended) | semantic | keyword
    """
    try:
        chunks = []

        if request.search_type == "keyword":
            chunks = es_service.keyword_search_chunks(
                es=es,
                query=request.question,
                source_filter=request.source_filter,
                top_k=request.top_k
            )

        elif request.search_type == "semantic":
            query_embedding = rag_service.embed_query(request.question)
            chunks = es_service.semantic_search_chunks(
                es=es,
                query_embedding=query_embedding,
                source_filter=request.source_filter,
                top_k=request.top_k
            )

        else:  # hybrid (default)
            query_embedding = rag_service.embed_query(request.question)
            chunks = es_service.hybrid_search_chunks(
                es=es,
                query=request.question,
                query_embedding=query_embedding,
                source_filter=request.source_filter,
                top_k=request.top_k
            )

        # Generate answer (plug in your LLM here)
        answer = rag_service.build_rag_answer(request.question, chunks)

        sources = [
            SourceChunk(
                content=c["content"],
                source=c["source"],
                page=c.get("page"),
                score=c["score"] or 0.0
            )
            for c in chunks
        ]

        return RAGQueryResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            search_type=request.search_type
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
def list_sources(es: Elasticsearch = Depends(get_es)):
    """List all ingested document sources and their chunk counts."""
    try:
        response = es.search(
            index=settings.chunks_index,
            aggs={
                "sources": {
                    "terms": {"field": "source", "size": 100}
                }
            },
            size=0
        )

        buckets = response["aggregations"]["sources"]["buckets"]
        return {
            "total_sources": len(buckets),
            "sources": [
                {"name": b["key"], "chunks": b["doc_count"]}
                for b in buckets
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
