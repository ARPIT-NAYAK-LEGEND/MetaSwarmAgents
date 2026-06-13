"""FastAPI backend serving the MetaSwarm dashboard and pipeline triggers."""

import asyncio
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from core.registry import get_registry
from core.orchestrator import Orchestrator


app = FastAPI(
    title="MetaSwarm API",
    description="Backend for the MetaSwarm self-evolving agent dashboard",
    version="1.0.0",
)

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global registry instance
registry = get_registry()




@app.get("/api/registry")
async def get_all_agents():
    """Return all agents with their current versions and history."""
    agents = registry.get_all_agents()
    return {"agents": agents}


@app.get("/api/traces/{run_id}")
async def get_traces(run_id: str):
    """Return all traces for a given run."""
    traces = registry.get_traces_for_run(run_id)
    return {"traces": traces}


@app.get("/api/stream")
async def stream_events():
    """
    Server-Sent Events (SSE) endpoint.

    Streams events to the dashboard in real-time.
    Includes a heartbeat ping every 15 seconds to keep the connection alive.
    """
    async def generate():
        last_timestamp = ""
        while True:
            try:
                events = registry.get_events_since(last_timestamp)
                for event in events:
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                    last_timestamp = event.get("timestamp", last_timestamp)
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            # Heartbeat to keep SSE alive (Azure load balancers close idle connections)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            await asyncio.sleep(1.5)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/api/run")
async def trigger_run(background_tasks: BackgroundTasks, full: bool = True):
    """
    Trigger a pipeline run.

    Args:
        full: If True, runs the full demo (fail → evolve → succeed).
              If False, runs only the worker pipeline.
    """
    def _run():
        spec_path = Path(__file__).resolve().parent.parent / "demo" / "spec.json"
        with open(spec_path, "r") as f:
            spec = json.load(f)

        task = {"spec": spec}
        orchestrator = Orchestrator(registry)

        if full:
            orchestrator.run_full_demo(task)
        else:
            orchestrator.run_worker_pipeline(task)

    # Run in background thread so the API responds immediately
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {
        "status": "started",
        "mode": "full" if full else "workers_only",
        "message": "Pipeline started. Watch /api/stream for real-time updates.",
    }


@app.post("/api/reset")
async def reset():
    """Reset the system to initial state for a fresh demo."""
    try:
        # Reset Controller Agent to v1.0
        registry.reset_agent_to_version("controller_agent", "1.0")

        # Clear traces and events
        registry.clear_traces_since(cutoff_minutes=60)
        if hasattr(registry, "clear_events"):
            registry.clear_events()

        # Emit reset event
        registry.emit_event({
            "type": "reset",
            "message": "Demo reset to initial state",
        })

        return {"status": "success", "message": "Reset complete. Controller Agent is v1.0."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
