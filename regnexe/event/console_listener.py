from __future__ import annotations

import json
from typing import Any

from regnexe.event.abstract_listener import AbstractEventListener


class ConsoleEventListener(AbstractEventListener):
    """Prints structured agent events to the console.

    Event types and their output format:

    - ``AGENT_STARTED``   → header banner
    - ``LLM_START``       → model call start + full message list sent to LLM
    - ``LLM_END``         → model response (+ token usage if show_token_usage=True)
    - ``TOOL_CALLED``     → tool invocation with input
    - ``TOOL_RESULT``     → tool result (truncated at 200 chars)
    - ``AGENT_COMPLETED`` → footer banner with status

    Args:
        show_system_prompt: Print the full system message (can be very long).
        show_llm_events:    Show LLM_START / LLM_END events (inherited filter).
        show_token_usage:   Print the ``tokens=`` line inside LLM_END.
        max_content_len:    Max chars shown per message content field.
    """

    def __init__(
        self,
        show_system_prompt: bool = False,
        show_llm_events: bool = False,
        show_token_usage: bool = False,
        max_content_len: int = 300,
    ) -> None:
        super().__init__(show_llm_events=show_llm_events or show_token_usage)
        self._show_system = show_system_prompt
        self._show_token = show_token_usage
        self._max_len = max_content_len

    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        match event_type:
            case "AGENT_STARTED":
                print(f"\n{'=' * 60}")
                print(f"[AGENT ▶] {name}")
                if goal := data.get("goal"):
                    print(f"          goal: {goal}")

            case "LLM_START":
                print(f"[LLM   ▶] {name}")
                for msg in data.get("messages", []):
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    tool_calls = msg.get("tool_calls")
                    tool_call_id = msg.get("tool_call_id")

                    if role == "system" and not self._show_system:
                        print(f"  [{role}] <{len(content)} chars — set show_system_prompt=True to display>")
                        continue

                    preview = self._truncate(content)
                    prefix = f"  [{role}]"
                    if tool_call_id:
                        prefix += f" (tool_call_id={tool_call_id})"
                    if preview:
                        print(f"{prefix} {preview}")
                    if tool_calls:
                        for tc in tool_calls:
                            args_str = json.dumps(tc.get("args", {}), ensure_ascii=False)
                            print(f"  [{role}→tool_call] {tc.get('name')}({args_str})")

            case "LLM_END":
                text = data.get("text", "")
                if self._show_token:
                    usage = data.get("usage") or {}
                    print(f"[LLM   ■] {name}  tokens={usage}")
                else:
                    print(f"[LLM   ■] {name}")
                if text:
                    print(f"          → {self._truncate(text)}")

            case "TOOL_CALLED":
                try:
                    input_str = json.dumps(data.get("input", {}), ensure_ascii=False)
                except (TypeError, ValueError):
                    input_str = str(data.get("input", ""))
                print(f"[TOOL  ▶] {self._label(name, data)}  input={input_str}")

            case "TOOL_RESULT":
                output = str(data.get("output", ""))
                print(f"[TOOL  ■] {self._label(name, data)}  output={self._truncate(output, 200)}")

            case "AGENT_COMPLETED":
                status = data.get("status", "unknown")
                print(f"[AGENT ■] status={status}")
                print(f"{'=' * 60}\n")

    def _truncate(self, text: str, max_len: int | None = None) -> str:
        n = max_len or self._max_len
        return text[:n] + ("..." if len(text) > n else "")

    @staticmethod
    def _label(name: str, data: dict[str, Any]) -> str:
        """Render "<type>:<name>" (e.g. "skill:travel_advisor"), prefixed with
        "[<type>:<name>] " when nested inside another subagent/skill's own execution.
        """
        cap_type = data.get("capability_type")
        label = f"{cap_type}:{name}" if cap_type else name
        nested_under = data.get("nested_under")
        if nested_under:
            label = f"[{nested_under['type']}:{nested_under['name']}] {label}"
        return label
