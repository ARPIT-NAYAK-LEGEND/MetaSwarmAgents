"""LLM client configuration for autogen-agentchat v0.7."""

import os
from pathlib import Path
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient, AzureOpenAIChatCompletionClient

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def get_model_client(temperature: float = 0.7) -> OpenAIChatCompletionClient:
    """
    Build an autogen v0.7 compatible model client.

    Args:
        temperature: LLM sampling temperature. Use 0 for deterministic agents.
    """
    # Check for Azure OpenAI first
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    if azure_key and azure_endpoint:
        return AzureOpenAIChatCompletionClient(
            model=azure_deployment,
            api_key=azure_key,
            azure_endpoint=azure_endpoint,
            api_version=azure_api_version,
            temperature=temperature,
        )

    # Fall back to OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return OpenAIChatCompletionClient(
            model=model,
            api_key=openai_key,
            temperature=temperature,
        )

    raise EnvironmentError(
        "No LLM credentials found. Set either OPENAI_API_KEY or "
        "AZURE_OPENAI_KEY + AZURE_OPENAI_ENDPOINT in your .env file."
    )


# Pre-built client factories for different agent roles
def get_deterministic_client():
    """For Observer, Bottleneck, Eval, Validator — temperature 0."""
    return get_model_client(temperature=0)


def get_creative_client():
    """For Refactor agent — temperature 0.3 for controlled creativity."""
    return get_model_client(temperature=0.3)


def get_worker_client():
    """For worker agents — temperature 0.7 for natural generation."""
    return get_model_client(temperature=0.7)
