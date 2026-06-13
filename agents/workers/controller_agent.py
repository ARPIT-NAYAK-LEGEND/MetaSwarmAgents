"""Controller Agent — generates Express.js handler functions.

Its system prompt is loaded from the registry so it picks up
any changes after a version promotion.
"""

from autogen_agentchat.agents import AssistantAgent
from core.registry import BaseRegistry
from core.config import get_worker_client


def build_controller_agent(registry: BaseRegistry) -> AssistantAgent:
    """Build the controller agent with its current registry prompt."""
    agent_doc = registry.get_agent("controller_agent")

    return AssistantAgent(
        name="controller_agent",
        model_client=get_worker_client(),
        system_message=agent_doc["system_prompt"],
    )
