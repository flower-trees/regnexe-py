"""Cross-session task result store — Layer 3 of the three-layer memory model."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskRecord:
    task_id: str
    goal: str
    summary: str
    status: str                                    # "completed" | "error" | "interrupted"
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskResultStore:
    """Stores task results so they can be surfaced in future sessions.

    Uses a LangGraph ``BaseStore`` when provided; falls back to in-process memory.
    Namespace layout in the store: ``(app_id, user_id, "task_history")``.
    """

    def __init__(self, store: Any | None = None) -> None:
        self._store = store
        self._memory: dict[str, list[TaskRecord]] = {}

    async def save(
        self,
        app_id: str,
        user_id: str,
        task_id: str,
        goal: str,
        summary: str,
        status: str = "completed",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = TaskRecord(
            task_id=task_id, goal=goal, summary=summary,
            status=status, metadata=metadata or {},
        )
        if self._store is not None:
            namespace = (app_id, user_id, "task_history")
            await self._store.aput(namespace, task_id, asdict(record))
        else:
            key = f"{app_id}:{user_id}"
            self._memory.setdefault(key, []).append(record)

    async def load_recent(self, app_id: str, user_id: str, n: int = 5) -> list[TaskRecord]:
        if self._store is not None:
            namespace = (app_id, user_id, "task_history")
            items = await self._store.asearch(namespace, limit=n)
            return [TaskRecord(**item.value) for item in items]
        key = f"{app_id}:{user_id}"
        records = self._memory.get(key, [])
        return sorted(records, key=lambda r: r.created_at, reverse=True)[:n]

    @staticmethod
    def format_for_prompt(records: list[TaskRecord]) -> str:
        """Format recent task records as a context block for the system prompt."""
        if not records:
            return ""
        lines = ["## Recent Task History"]
        for r in records:
            lines.append(f"- [{r.status}] {r.goal}: {r.summary}")
        return "\n".join(lines)
