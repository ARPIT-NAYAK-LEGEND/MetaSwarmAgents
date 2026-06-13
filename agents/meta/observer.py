"""Post-run quality scorer for worker agents."""

import json
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry
from core.config import get_deterministic_client


OBSERVER_SYSTEM_PROMPT = """You are a multi-agent quality evaluator.
You receive execution traces from a 5-agent pipeline and score each agent 0-100.

Scoring criteria:
- spec_parser: Did it correctly extract all operationIds and their requirements? 
- route_builder: Is the Express scaffolding syntactically valid and complete?
- controller_agent: Do handlers implement real logic (not stubs)? Are TODOs absent?
- test_generator: Are tests specific to the operations, not generic templates?
- validator: Did it correctly identify pass/fail and give accurate counts?

Respond ONLY with this JSON structure, no explanation:
{
  "scores": {
    "spec_parser": N,
    "route_builder": N,
    "controller_agent": N,
    "test_generator": N,
    "validator": N
  },
  "analysis": {
    "spec_parser": "one sentence",
    "route_builder": "one sentence",
    "controller_agent": "one sentence",
    "test_generator": "one sentence",
    "validator": "one sentence"
  }
}"""


async def _run_observer_async(registry: BaseRegistry, run_id: str) -> dict:
    """Score all agents from a failed run using the Observer."""
    traces = registry.get_traces_for_run(run_id)

    if not traces:
        raise ValueError(f"No traces found for run {run_id}")

    trace_summary = "\n\n".join([
        f"=== {t['agent']} (v{t['version']}) ===\n"
        f"INPUT:\n{t['input'][:500]}\n"
        f"OUTPUT:\n{t['output'][:800]}"
        for t in traces
    ])

    observer = AssistantAgent(
        "observer",
        model_client=get_deterministic_client(),
        system_message=OBSERVER_SYSTEM_PROMPT,
    )

    msg = TextMessage(
        content=f"Score these agent traces from a pipeline run:\n\n{trace_summary}",
        source="user",
    )
    response = await observer.on_messages([msg], CancellationToken())

    raw = response.chat_message.to_text()

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    return json.loads(cleaned)


def run_observer(registry: BaseRegistry, run_id: str) -> dict:
    """Score all agents (blocking call)."""
    return asyncio.run(_run_observer_async(registry, run_id))
