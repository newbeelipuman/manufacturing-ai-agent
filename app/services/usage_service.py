from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import UsageStat


def record_usage(
    db: Session,
    username: str,
    role: str,
    tool_call_count: int = 0,
    estimated_tokens: int = 0,
) -> UsageStat:
    today = date.today()
    stat = db.scalar(
        select(UsageStat).where(
            UsageStat.username == username,
            UsageStat.role == role,
            UsageStat.date == today,
        )
    )
    if not stat:
        stat = UsageStat(
            username=username,
            role=role,
            date=today,
            request_count=0,
            tool_call_count=0,
            estimated_tokens=0,
        )
        db.add(stat)

    stat.request_count += 1
    stat.tool_call_count += tool_call_count
    stat.estimated_tokens += estimated_tokens
    db.commit()
    db.refresh(stat)
    return stat
