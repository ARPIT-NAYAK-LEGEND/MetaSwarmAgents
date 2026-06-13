"""Writes Jest tests for the generated Express.js handlers."""

from autogen_agentchat.agents import AssistantAgent
from core.config import get_worker_client


def build_test_generator() -> AssistantAgent:
    """Set up the test generator agent."""
    return AssistantAgent(
        name="test_generator",
        model_client=get_worker_client(),
        system_message=(
            "You are a Jest test writer for Express.js APIs. Given handler code, "
            "write comprehensive Jest tests using supertest. Cover happy paths, "
            "edge cases, and error handling. Each test must assert specific status "
            "codes and response shapes. Be thorough — write tests for every operation."
        ),
    )
