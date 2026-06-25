from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app


CASES = [
    ("订单发货风险", "sales", "订单 O1001 现在能不能发货？"),
    ("订单发货风险", "normal_user", "订单 O1001 现在能不能发货？"),
    ("订单发货风险", "admin", "订单 O1001 现在能不能发货？"),
    ("SOP 查询", "normal_user", "注塑件外观不良应该怎么处理？"),
    ("SOP 查询", "admin", "注塑件外观不良应该怎么处理？"),
    ("采购延期影响", "purchase", "采购单 PO1001 延期会影响哪些客户订单？"),
    ("采购延期影响", "normal_user", "采购单 PO1001 延期会影响哪些客户订单？"),
    ("采购延期影响", "admin", "采购单 PO1001 延期会影响哪些客户订单？"),
]


def _print_trace(trace: list[dict]) -> None:
    for row in trace:
        step = row.get("step", "-")
        status = row.get("status", "-")
        tool_name = row.get("tool_name")
        if tool_name:
            print(f"  - {step}: {tool_name} {status}")
        else:
            print(f"  - {step}: {status}")


def main() -> None:
    with TestClient(app) as client:
        for title, role, question in CASES:
            response = client.post(
                "/api/chat",
                json={"username": f"demo_{role}", "role": role, "question": question},
            )
            body = response.json()
            print("=" * 60)
            print(f"Case: {title} / {role}")
            print(f"Question: {question}")
            print(f"HTTP Status: {response.status_code}")
            print(f"Intent: {body.get('intent')}")
            print(f"Entities: {body.get('entities')}")
            print(f"Risk Level: {body.get('risk_level')}")
            print("Trace:")
            _print_trace(body.get("execution_trace", []))
            print("Answer:")
            print(body.get("answer", ""))
        print("=" * 60)


if __name__ == "__main__":
    main()
