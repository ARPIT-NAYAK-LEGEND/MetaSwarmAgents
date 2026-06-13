"""Static-analysis validator that scores handlers against their tests."""

from autogen_agentchat.agents import AssistantAgent
from core.config import get_deterministic_client


def build_validator() -> AssistantAgent:
    """Validator uses temperature=0 for reproducible scoring."""
    return AssistantAgent(
        name="validator",
        model_client=get_deterministic_client(),
        system_message=(
            "You are a code quality validator. Given Express.js handler code and Jest tests, "
            "evaluate whether the handlers would pass the tests. Consider: Does each handler "
            "implement real logic or just stubs? Are edge cases handled? Do response shapes "
            "match what tests expect? Respond ONLY with JSON: "
            '{\"passed\": N, \"total\": N, \"score\": N, \"failures\": [\"description\"]}'
        ),
    )
