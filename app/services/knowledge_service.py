from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.rag.retriever import search_sop_chunks


SOP_DIR = Path("docs/sop")


def _split_text(text: str, chunk_size: int = 800) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) > chunk_size and current:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current.strip())
    return chunks or [text.strip()]


def rebuild_knowledge(db: Session) -> dict[str, Any]:
    db.execute(delete(KnowledgeChunk))
    db.execute(delete(KnowledgeDocument))

    documents = 0
    chunks = 0
    for path in sorted(SOP_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else path.stem
        document = KnowledgeDocument(
            title=title,
            doc_type="sop",
            source_path=str(path.as_posix()),
            status="active",
        )
        db.add(document)
        db.flush()
        documents += 1
        for index, chunk_text in enumerate(_split_text(text)):
            db.add(
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_text=chunk_text,
                    chunk_index=index,
                    metadata_json={"source": str(path.as_posix())},
                )
            )
            chunks += 1

    db.commit()
    return {"documents": documents, "chunks": chunks}


def search_knowledge(db: Session, query: str) -> list[dict[str, Any]]:
    return search_sop_chunks(db=db, query=query, limit=5)
