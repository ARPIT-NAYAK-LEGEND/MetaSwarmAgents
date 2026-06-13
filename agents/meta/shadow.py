"""A/B shadow run: replays the original inputs through the v2.0 candidate prompt."""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry
from core.config import get_worker_client


async def _run_shadow_async(registry: BaseRegistry, run_id: str) -> str:
    """Execute the v2.0 candidate prompt against the same inputs as the failed run."""
    original_trace = registry.get_trace(run_id, "controller_agent")
    if original_trace is None:
        raise ValueError(f"No controller_agent trace found for run {run_id}")

    original_input = original_trace["input"]
    new_prompt = registry.get_candidate_prompt("controller_agent", "2.0")

    shadow = AssistantAgent(
        "controller_agent_shadow",
        model_client=get_worker_client(),
        system_message=new_prompt,
    )

    msg = TextMessage(content=original_input, source="user")
    response = await shadow.on_messages([msg], CancellationToken())

    shadow_output = response.chat_message.to_text()
    registry.save_shadow_output(run_id, "controller_agent", "2.0", shadow_output)

    return shadow_output


def run_shadow(registry: BaseRegistry, run_id: str) -> str:
    """Execute the shadow A/B test (blocking)."""
    return asyncio.run(_run_shadow_async(registry, run_id))
