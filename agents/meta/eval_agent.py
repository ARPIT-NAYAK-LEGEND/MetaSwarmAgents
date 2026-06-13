"""Rubric-based comparison of v1 vs v2 controller output."""

import json
import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry
from core.config import get_deterministic_client
from core.rubric import EVAL_RUBRIC_PROMPT


async def _run_eval_async(registry: BaseRegistry, run_id: str, spec: str) -> dict:
    """Compare v1.0 and v2.0 outputs using the rubric and return scored results."""
    v1_output = registry.get_trace(run_id, "controller_agent")["output"]
    v2_output = registry.get_shadow_output(run_id, "controller_agent", "2.0")

    message = f"""Spec:
{spec}

Controller v1.0 output:
{v1_output[:3000]}

Controller v2.0 output:
{v2_output[:3000]}

Score both versions."""

    eval_agent = AssistantAgent(
        "eval_agent",
        model_client=get_deterministic_client(),
        system_message=EVAL_RUBRIC_PROMPT,
    )

    msg = TextMessage(content=message, source="user")
    response = await eval_agent.on_messages([msg], CancellationToken())
    raw = response.chat_message.to_text()

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    result = json.loads(cleaned)
    return result


def run_eval(registry: BaseRegistry, run_id: str, spec: str) -> dict:
    """Blocking wrapper around the async eval comparison."""
    return asyncio.run(_run_eval_async(registry, run_id, spec))
