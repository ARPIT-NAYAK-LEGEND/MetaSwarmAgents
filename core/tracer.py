"""Wraps agent calls to log I/O, timing, and version info to the registry."""

import time
import asyncio
from datetime import datetime, timezone

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry


async def call_traced_agent(
    agent: AssistantAgent,
    message: str,
    *,
    agent_id: str,
    registry: BaseRegistry,
    run_id: str,
) -> str:
    """
    Call an agent and trace the I/O to the registry.

    Args:
        agent: The AssistantAgent to call.
        message: The user message to send.
        agent_id: Registry ID for this agent.
        registry: The registry to log traces to.
        run_id: The current pipeline run ID.

    Returns:
        The agent's text response.
    """
    start = time.time()

    user_msg = TextMessage(content=message, source="user")
    cancellation_token = CancellationToken()

    response = await agent.on_messages([user_msg], cancellation_token)

    elapsed_ms = int((time.time() - start) * 1000)

    output_text = ""
    if response.chat_message:
        output_text = response.chat_message.to_text()

    try:
        registry.log_trace({
            "id": f"trace_{run_id}_{agent_id}_{int(start)}",
            "run_id": run_id,
            "agent": agent_id,
            "version": registry.get_agent_version(agent_id),
            "input": message[:2000],  # Cap input length
            "output": output_text[:5000],  # Cap output length
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": elapsed_ms,
        })
    except Exception as e:
        print(f"  ⚠ Tracing error for {agent_id}: {e}")

    return output_text


def call_traced_agent_sync(
    agent: AssistantAgent,
    message: str,
    *,
    agent_id: str,
    registry: BaseRegistry,
    run_id: str,
) -> str:
    """Synchronous wrapper for call_traced_agent."""
    return asyncio.run(call_traced_agent(
        agent, message,
        agent_id=agent_id,
        registry=registry,
        run_id=run_id,
    ))
