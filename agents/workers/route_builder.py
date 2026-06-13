"""Generates Express.js route scaffolding from parsed operations."""

from autogen_agentchat.agents import AssistantAgent
from core.config import get_worker_client


def build_route_builder() -> AssistantAgent:
    """Create the route builder agent."""
    return AssistantAgent(
        name="route_builder",
        model_client=get_worker_client(),
        system_message=(
            "You are an Express.js route generator. Given a list of API operations "
            "(method, path, operationId), generate a complete Express.js router file. "
            "Include proper imports, route definitions with placeholder handler references, "
            "and module.exports. Use RESTful conventions."
        ),
    )
