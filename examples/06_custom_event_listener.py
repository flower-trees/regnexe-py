"""Example 06 — Custom AgentEventListener: structured JSON logging + token aggregation

Demonstrates how to implement a custom AgentEventListener that:
  1. Writes structured JSON log lines to a file (machine-readable audit trail)
  2. Aggregates token usage across all LLM calls in a single invocation
  3. Reports cost metrics at the end of each task

Use case: production observability -- feed JSON logs into ELK, Loki, or any log aggregator.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

from regnexe import RegnexeAgentBuilder, Vendor, agent_tool, plugin


@dataclass
class _UsageAccumulator:
    input_tokens: int = 0
    output_tokens: int = 0
    llm_calls: int = 0
    tool_calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class JsonFileEventListener:
    """Writes every agent event as a JSON line and tracks cumulative token usage."""

    def __init__(self, log_path: str = "/tmp/regnexe_agent.jsonl") -> None:
        self._log_path = log_path
        self._usage = _UsageAccumulator()
        self._start_ts = time.time()

    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        elapsed = round(time.time() - self._start_ts, 3)
        record: dict[str, Any] = {"ts": elapsed, "event": event_type, "name": name}

        match event_type:
            case "AGENT_STARTED":
                record["goal"] = data.get("goal", "")
                print(f"[START] task started -- log: {self._log_path}")

            case "LLM_START":
                self._usage.llm_calls += 1
                record["message_count"] = len(data.get("messages", []))

            case "LLM_END":
                usage = data.get("usage") or {}
                in_tok = usage.get("input_tokens", 0)
                out_tok = usage.get("output_tokens", 0)
                self._usage.input_tokens += in_tok
                self._usage.output_tokens += out_tok
                record["input_tokens"] = in_tok
                record["output_tokens"] = out_tok

            case "TOOL_CALLED":
                self._usage.tool_calls += 1
                record["tool_input"] = data.get("input", {})

            case "TOOL_RESULT":
                output = str(data.get("output", ""))
                record["output_len"] = len(output)

            case "AGENT_COMPLETED":
                record["status"] = data.get("status")
                record["summary"] = {
                    "llm_calls": self._usage.llm_calls,
                    "tool_calls": self._usage.tool_calls,
                    "input_tokens": self._usage.input_tokens,
                    "output_tokens": self._usage.output_tokens,
                    "total_tokens": self._usage.total_tokens,
                    "elapsed_s": round(time.time() - self._start_ts, 2),
                }
                self._print_summary()

        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _print_summary(self) -> None:
        u = self._usage
        elapsed = round(time.time() - self._start_ts, 2)
        print(
            f"\n{'─' * 50}\n"
            f"Task completed in {elapsed}s\n"
            f"  LLM calls  : {u.llm_calls}\n"
            f"  Tool calls : {u.tool_calls}\n"
            f"  Tokens in  : {u.input_tokens}\n"
            f"  Tokens out : {u.output_tokens}\n"
            f"  Total      : {u.total_tokens}\n"
            f"{'─' * 50}"
        )


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        data = {
            "Beijing": "sunny, 22 degrees C, excellent air quality",
            "Shanghai": "cloudy, 18 degrees C, moderate humidity",
        }
        return data.get(city, f"No data for {city}")


async def main() -> None:
    log_path = "/tmp/regnexe_agent.jsonl"
    listener = JsonFileEventListener(log_path=log_path)

    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(listener)
        .build()
    )

    result = await agent.ainvoke(
        "Compare the weather in Beijing and Shanghai today. Which city is better for a jog?",
        app_id="demo", user_id="user1", session_id="sess-custom-log",
    )

    print("\nFinal answer:", result.final_text)
    print(f"\nJSON log written to: {log_path}")
    print("Last 3 log lines:")
    with open(log_path) as f:
        lines = f.readlines()
        for line in lines[-3:]:
            print(" ", line.rstrip())


if __name__ == "__main__":
    asyncio.run(main())
