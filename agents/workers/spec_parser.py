"""Extracts operations from an OpenAPI spec."""

from autogen_agentchat.agents import AssistantAgent
from core.config import get_worker_client


def build_spec_parser() -> AssistantAgent:
    """Return a configured spec parser agent."""
    return AssistantAgent(
        name="spec_parser",
        model_client=get_worker_client(),
        system_message=(
            "You are an OpenAPI spec parser. Given an OpenAPI JSON spec, extract all operations. "
            "For each operation, output the HTTP method, path, operationId, and full summary. "
            "Output as a structured list. Be thorough — miss nothing."
        ),
    )
