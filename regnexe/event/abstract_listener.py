from __future__ import annotations

from regnexe.event.listener import AgentEventListener

_LLM_EVENTS = ("LLM_START", "LLM_END")


class AbstractEventListener(AgentEventListener):
    """Convenience base class for custom AgentEventListener implementations.

    Subclasses inherit built-in filtering via constructor flags and only need
    to implement on_event(); no need to override should_handle() for the
    common LLM suppression case.

    Args:
        show_llm_events: If False (default), LLM_START and LLM_END events are
            suppressed before on_event() is called.

    Example::

        class MyListener(AbstractEventListener):
            def __init__(self):
                super().__init__(show_llm_events=False)

            async def on_event(self, event_type, name, data):
                ...   # never receives LLM_START / LLM_END
    """

    def __init__(self, show_llm_events: bool = False) -> None:
        self._show_llm = show_llm_events

    def should_handle(self, event_type: str) -> bool:
        if not self._show_llm and event_type in _LLM_EVENTS:
            return False
        return True
