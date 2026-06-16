from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AgentEventListener(ABC):
    """Base interface for all agent event listeners.

    The framework calls :meth:`dispatch` (not :meth:`on_event` directly), so
    subclasses can filter events by overriding :meth:`should_handle` without
    touching the dispatch path.

    Lambda / simple implementations only need to provide :meth:`on_event`.
    For built-in token / LLM filtering, extend :class:`AbstractEventListener`.
    """

    def should_handle(self, event_type: str) -> bool:
        """Return False to prevent on_event from being called for this event type.

        Default: handle every event.
        """
        return True

    async def dispatch(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        """Framework entry point. Checks should_handle() before calling on_event()."""
        if self.should_handle(event_type):
            await self.on_event(event_type, name, data)

    @abstractmethod
    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None: ...
