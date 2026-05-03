import io
import pdfplumber
from pathlib import Path
from typing import Optional
from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()

# Load embedding model once at startup
_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def embed_query(query: str) -> list[float]:
    """Generate embedding for a single query string."""
    model = get_embedding_model()
    return model.encode([query])[0].tolist()


# ─── PDF Processing ───────────────────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> list[dict]:
    """Extract text from PDF bytes, page by page."""
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "page": page_num,
                    "text": text.strip()
                })
    return pages


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.
    Tries to break at sentence boundaries for cleaner chunks.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to end at a sentence boundary
        if end < text_len:
            last_period = text.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunk = text[start:end].strip()
        if len(chunk) > 50:   # ignore tiny chunks
            chunks.append(chunk)

        start = end - overlap

    return chunks


def pdf_bytes_to_chunks(
    file_bytes: bytes,
    filename: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[dict]:
    """
    Full pipeline: PDF bytes → chunked documents with metadata.
    Each chunk is ready to be indexed into Elasticsearch.
    """
    source_name = Path(filename).stem
    pages = extract_pdf_text(file_bytes)

    all_chunks = []
    chunk_id = 0

    for page_data in pages:
        chunks = chunk_text(page_data['text'], chunk_size, overlap)
        for chunk_text_content in chunks:
            all_chunks.append({
                "chunk_id": chunk_id,
                "source": source_name,
                "source_type": "pdf",
                "page": page_data['page'],
                "content": chunk_text_content,
                "content_length": len(chunk_text_content)
            })
            chunk_id += 1

    return all_chunks


def add_embeddings_to_chunks(chunks: list[dict]) -> list[dict]:
    """
    Generate and attach embeddings to each chunk.
    This enables vector/semantic search.
    """
    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts)

    enriched = []
    for chunk, embedding in zip(chunks, embeddings):
        enriched_chunk = chunk.copy()
        enriched_chunk["embedding"] = embedding
        enriched.append(enriched_chunk)

    return enriched


# ─── Answer Generation ────────────────────────────────────────────────────────

def build_rag_answer(question: str, chunks: list[dict]) -> str:
    """
    Build an answer from retrieved chunks.

    In a real app, pass the context to an LLM (Claude, GPT, etc.).
    Here we return a structured "answer" showing what would be sent.
    """
    if not chunks:
        return "No relevant information found in the indexed documents."

    # Build context string
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[Source: {chunk['source']}"
        if chunk.get('page'):
            source_info += f", Page {chunk['page']}"
        source_info += "]"
        context_parts.append(f"{source_info}\n{chunk['content']}")

    context = "\n\n---\n\n".join(context_parts)

    # This is the prompt you'd send to an LLM
    prompt = f"""Answer the question based ONLY on the following context from the documents.
If the answer cannot be found in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {question}

Answer:"""

    # ── Plug in your LLM here ──────────────────────────────────────
    # For Claude:
    # import anthropic
    # client = anthropic.Anthropic()
    # message = client.messages.create(
    #     model="claude-opus-4-6",
    #     max_tokens=1024,
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return message.content[0].text
    #
    # For OpenAI:
    # from openai import OpenAI
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return response.choices[0].message.content
    # ──────────────────────────────────────────────────────────────

    # Placeholder answer (remove when you integrate an LLM)
    return (
        f"[LLM integration placeholder]\n\n"
        f"Retrieved {len(chunks)} relevant chunks. "
        f"Integrate an LLM (Claude/GPT) to generate a proper answer.\n\n"
        f"The prompt sent to the LLM would be:\n\n{prompt[:500]}..."
    )
