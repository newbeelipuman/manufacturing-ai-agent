from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument


DOMAIN_TERMS = [
    "注塑件",
    "外观不良",
    "采购延期",
    "交期异常",
    "库存不足",
    "不能发货",
    "工单缺料",
    "缺料",
    "开工",
    "客户订单",
    "沟通",
    "质量",
    "冻结",
]


def _tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9_-]+", text)]
    for term in DOMAIN_TERMS:
        if term in text:
            tokens.append(term)
    return tokens


def search_sop_chunks(db: Session, query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search SOP chunks with a local TF-IDF style score and matched terms."""
    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeDocument.status == "active")
    ).all()
    if not rows:
        return []

    docs: list[tuple[KnowledgeChunk, KnowledgeDocument, list[str]]] = []
    doc_freq: Counter[str] = Counter()
    for chunk, doc in rows:
        tokens = _tokenize(f"{doc.title}\n{chunk.chunk_text}")
        unique_tokens = set(tokens)
        doc_freq.update(unique_tokens)
        docs.append((chunk, doc, tokens))

    query_terms = _tokenize(query)
    query_counter = Counter(query_terms)
    total_docs = len(docs)
    scored: list[tuple[float, list[str], KnowledgeChunk, KnowledgeDocument]] = []
    for chunk, doc, tokens in docs:
        token_counter = Counter(tokens)
        matched_terms = [term for term in query_counter if token_counter.get(term, 0) > 0]
        if not matched_terms:
            continue
        score = 0.0
        for term in matched_terms:
            tf = token_counter[term]
            idf = math.log((1 + total_docs) / (1 + doc_freq[term])) + 1
            score += tf * idf * query_counter[term]
        scored.append((score, matched_terms, chunk, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "doc_title": doc.title,
            "title": doc.title,
            "doc_type": doc.doc_type,
            "source_path": doc.source_path,
            "chunk_index": chunk.chunk_index,
            "score": round(score, 4),
            "matched_terms": matched_terms,
            "chunk_text": chunk.chunk_text,
        }
        for score, matched_terms, chunk, doc in scored[:limit]
    ]
