"""Generates an improved system prompt for the agent identified by Bottleneck."""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry
from core.config import get_creative_client


REFACTOR_SYSTEM_PROMPT = """You are a system prompt engineer for AI agents.
You receive a failing agent's current system prompt and a root cause analysis of why it failed.
Your job: write an improved system prompt that addresses the root cause.

Rules:
1. Keep everything that works in the original prompt
2. Add the missing instruction identified in the root cause analysis
3. Be concrete and specific — avoid vague instructions like "be thorough"
4. Do not add more than 3 new sentences to the original prompt
5. The improved prompt must instruct the agent to use its full input context
6. Preserve the structure and tone of the original prompt
7. Do not remove any existing instruction — only add the identified missing capability

Respond ONLY with the new system prompt text, nothing else. No preamble, no explanation."""


async def _run_refactor_async(registry: BaseRegistry, bottleneck_result: dict) -> str:
    """Generate an improved system prompt for the identified failing agent."""
    agent_doc = registry.get_agent(bottleneck_result["failing_agent"])
    original_prompt = agent_doc["system_prompt"]

    message = f"""Current system prompt:
{original_prompt}

Root cause analysis:
{bottleneck_result['root_cause']}

Missing instruction:
{bottleneck_result['missing_instruction']}

Write the improved system prompt."""

    refactor = AssistantAgent(
        "refactor",
        model_client=get_creative_client(),
        system_message=REFACTOR_SYSTEM_PROMPT,
    )

    msg = TextMessage(content=message, source="user")
    response = await refactor.on_messages([msg], CancellationToken())
    new_prompt = response.chat_message.to_text().strip()

    if new_prompt.startswith("```"):
        new_prompt = new_prompt.split("\n", 1)[1]
        if new_prompt.endswith("```"):
            new_prompt = new_prompt[:-3]
        new_prompt = new_prompt.strip()

    registry.save_candidate_prompt(
        bottleneck_result["failing_agent"],
        "2.0",
        new_prompt,
    )

    return new_prompt


def run_refactor(registry: BaseRegistry, bottleneck_result: dict) -> str:
    """Run prompt refactoring synchronously and return the new prompt."""
    return asyncio.run(_run_refactor_async(registry, bottleneck_result))
