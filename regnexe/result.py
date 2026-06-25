from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    status: str        # "completed" | "error" | "interrupted" | "cancelled"
    final_text: str
    task_id: str
    thread_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
