"""Root-cause analysis: pinpoints which agent caused a pipeline failure."""

import json
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry
from core.config import get_deterministic_client


BOTTLENECK_SYSTEM_PROMPT = """You are a root cause analysis agent for a multi-agent pipeline failure.
You receive agent quality scores and their execution traces.
Identify the single agent most responsible for the task failure.

Respond ONLY with this JSON:
{
  "failing_agent": "agent_id",
  "version": "X.Y",
  "score": N,
  "root_cause": "One precise sentence describing what the system prompt fails to instruct.",
  "missing_instruction": "The exact capability or instruction that must be added to the system prompt."
}

Be specific in missing_instruction. Not 'add business logic' but 'instruct the agent to read operationId summaries from the spec and implement the described logic in each handler'."""


async def _run_bottleneck_async(registry: BaseRegistry, run_id: str, observer_result: dict) -> dict:
    """Pinpoint the failing agent given Observer scores and traces."""
    traces = registry.get_traces_for_run(run_id)

    trace_summary = "\n\n".join([
        f"=== {t['agent']} (v{t['version']}) ===\n"
        f"INPUT:\n{t['input'][:300]}\n"
        f"OUTPUT:\n{t['output'][:500]}"
        for t in traces
    ])

    message = f"""Agent scores:
{json.dumps(observer_result['scores'], indent=2)}

Agent analysis:
{json.dumps(observer_result.get('analysis', {}), indent=2)}

Trace data:
{trace_summary}

Identify the single failing agent and its root cause."""

    bottleneck = AssistantAgent(
        "bottleneck",
        model_client=get_deterministic_client(),
        system_message=BOTTLENECK_SYSTEM_PROMPT,
    )

    msg = TextMessage(content=message, source="user")
    response = await bottleneck.on_messages([msg], CancellationToken())
    raw = response.chat_message.to_text()

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    return json.loads(cleaned)


def run_bottleneck(registry: BaseRegistry, run_id: str, observer_result: dict) -> dict:
    """Run bottleneck analysis synchronously."""
    return asyncio.run(_run_bottleneck_async(registry, run_id, observer_result))
