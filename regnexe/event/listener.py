from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AgentEventListener(Protocol):
    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None: ...
