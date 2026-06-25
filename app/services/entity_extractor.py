import re
from typing import Any


PATTERNS: dict[str, str] = {
    "order_no": r"\bO\d+\b",
    "work_order_no": r"\bWO\d+\b",
    "purchase_order_no": r"\bPO\d+\b",
    "sku_code": r"\bSKU-[A-Z0-9-]+\b",
    "batch_no": r"\bBATCH-[A-Z0-9-]+\b",
}


def extract_entities(question: str) -> dict[str, Any]:
    """Extract manufacturing identifiers from a natural-language question."""
    entities: dict[str, Any] = {}
    for name, pattern in PATTERNS.items():
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match:
            entities[name] = match.group(0).upper()
    return entities
