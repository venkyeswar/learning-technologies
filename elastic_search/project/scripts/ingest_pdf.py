"""
CLI tool to ingest a PDF into Elasticsearch.
Usage: python scripts/ingest_pdf.py path/to/document.pdf
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.es_service import get_es_client, setup_indices, index_chunks
from app.services.rag_service import pdf_bytes_to_chunks, add_embeddings_to_chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_pdf.py <path-to-pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)

    print(f"📄 Ingesting: {pdf_path}")
    es = get_es_client()

    if not es.ping():
        print("❌ Cannot connect to Elasticsearch.")
        sys.exit(1)

    setup_indices(es)

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(pdf_path)

    print("  → Extracting and chunking text...")
    chunks = pdf_bytes_to_chunks(file_bytes, filename)
    print(f"  → Created {len(chunks)} chunks")

    print("  → Generating embeddings (this may take a moment)...")
    chunks_with_embeddings = add_embeddings_to_chunks(chunks)

    print("  → Indexing into Elasticsearch...")
    success, failed = index_chunks(es, chunks_with_embeddings)

    print(f"\n✅ Done! Indexed {success} chunks from '{filename}'.")
    print("\nNow query it:")
    print('  curl -X POST http://localhost:8000/api/rag/query \\')
    print('    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"question": "What is this document about?", "source_filter": "{os.path.splitext(filename)[0]}"}}\' ')


if __name__ == "__main__":
    main()
