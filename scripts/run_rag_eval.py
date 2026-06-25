from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.session import SessionLocal
from app.rag.retriever import search_sop_chunks
from scripts.seed_demo_data import seed_demo_data


REPORT_PATH = ROOT_DIR / "docs" / "rag-eval-report.md"

CASES = [
    {
        "query": "注塑件外观不良应该怎么处理？",
        "expected_source": "docs/sop/injection_appearance_exception.md",
    },
    {
        "query": "采购延期应该怎么沟通？",
        "expected_source": "docs/sop/purchase_delay_communication.md",
    },
    {
        "query": "订单库存不足导致不能发货怎么办？",
        "expected_source": "docs/sop/order_delivery_exception.md",
    },
    {
        "query": "工单缺料不能开工怎么办？",
        "expected_source": "docs/sop/work_order_material_shortage.md",
    },
    {
        "query": "订单交期异常应该怎么处理？",
        "expected_source": "docs/sop/order_delivery_exception.md",
    },
]


def _evaluate() -> list[dict[str, Any]]:
    seed_demo_data()
    db = SessionLocal()
    try:
        results: list[dict[str, Any]] = []
        for case in CASES:
            matches = search_sop_chunks(db=db, query=case["query"], limit=3)
            top = matches[0] if matches else {}
            top_source = top.get("source_path", "")
            results.append(
                {
                    "query": case["query"],
                    "expected_source": case["expected_source"],
                    "top_source": top_source,
                    "score": top.get("score", 0),
                    "matched_terms": top.get("matched_terms", []),
                    "passed": top_source == case["expected_source"],
                }
            )
        return results
    finally:
        db.close()


def _report(results: list[dict[str, Any]]) -> str:
    lines = [
        "# RAG Eval Report",
        "",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "本报告由 `python scripts/run_rag_eval.py` 生成。评估使用本地模拟 SOP 文档和轻量 TF-IDF 风格检索，不调用外部 LLM。",
        "",
        "| query | expected_source | top_source | score | matched_terms | passed |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in results:
        matched_terms = ", ".join(str(term) for term in row["matched_terms"])
        lines.append(
            f"| {row['query']} | `{row['expected_source']}` | `{row['top_source']}` | "
            f"{row['score']} | {matched_terms} | {row['passed']} |"
        )
    passed = sum(1 for row in results if row["passed"])
    lines.extend(
        [
            "",
            f"Passed: {passed}/{len(results)}",
            "",
            "边界：当前仍是 MVP 原型，知识来源为本地模拟 SOP，不接入真实企业知识库或 ERP/MES/WMS。",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    results = _evaluate()
    REPORT_PATH.write_text(_report(results), encoding="utf-8")
    print(f"RAG eval report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
