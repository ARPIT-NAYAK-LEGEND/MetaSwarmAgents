"""Central data layer for MetaSwarm.

Two implementations share a common ABC:
- LocalRegistry (JSON file storage, default)
- CosmosRegistry (Azure Cosmos DB)
"""

import json
import os
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BaseRegistry(ABC):
    """Interface for all registry implementations."""



    @abstractmethod
    def get_agent(self, agent_id: str) -> dict:
        """Get an agent document by ID."""

    @abstractmethod
    def get_all_agents(self) -> list[dict]:
        """Get all agent documents."""

    @abstractmethod
    def upsert_agent(self, agent_doc: dict) -> None:
        """Insert or update an agent document."""

    @abstractmethod
    def get_agent_version(self, agent_id: str) -> str:
        """Get the current version string for an agent."""



    @abstractmethod
    def log_trace(self, trace: dict) -> None:
        """Log an agent execution trace."""

    @abstractmethod
    def get_traces_for_run(self, run_id: str) -> list[dict]:
        """Get all traces for a given run."""

    @abstractmethod
    def get_trace(self, run_id: str, agent_id: str) -> dict | None:
        """Get a specific agent's trace from a run."""


    @abstractmethod
    def save_run_result(self, result: dict) -> None:
        """Save the result of a pipeline run."""



    @abstractmethod
    def save_candidate_prompt(self, agent_id: str, version: str, prompt: str) -> None:
        """Save a candidate system prompt (not yet promoted)."""

    @abstractmethod
    def get_candidate_prompt(self, agent_id: str, version: str) -> str:
        """Retrieve a candidate system prompt."""



    @abstractmethod
    def save_shadow_output(self, run_id: str, agent_id: str, version: str, output: str) -> None:
        """Save the output from a shadow (v2.0) run."""

    @abstractmethod
    def get_shadow_output(self, run_id: str, agent_id: str, version: str) -> str:
        """Get the shadow output for comparison."""



    @abstractmethod
    def promote_agent(self, agent_id: str, version: str, new_prompt: str, eval_score: float) -> None:
        """Promote an agent to a new version. Updates current_version and system_prompt."""

    @abstractmethod
    def reset_agent_to_version(self, agent_id: str, version: str) -> None:
        """Reset an agent back to a specific version (for demo resets)."""



    @abstractmethod
    def emit_event(self, event: dict) -> None:
        """Emit an event for the dashboard to consume."""

    @abstractmethod
    def get_events_since(self, timestamp: str) -> list[dict]:
        """Get all events since a given ISO timestamp."""



    @abstractmethod
    def clear_traces_since(self, cutoff_minutes: int) -> None:
        """Clear traces newer than cutoff_minutes ago."""


class LocalRegistry(BaseRegistry):
    """
    JSON file-based registry for local development.

    Data is stored under a `data/` directory:
      data/agents/{agent_id}.json
      data/traces/{run_id}/{agent_id}.json
      data/candidates/{agent_id}_{version}.json
      data/shadows/{run_id}_{agent_id}_{version}.json
      data/events/events.json
      data/runs/{run_id}.json
    """

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent / "data"
        self.data_dir = Path(data_dir)
        self._lock = threading.Lock()
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create all required subdirectories."""
        for subdir in ["agents", "traces", "candidates", "shadows", "events", "runs"]:
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> dict | list | None:
        """Thread-safe JSON file read."""
        if not path.exists():
            return None
        with self._lock:
            return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data: Any) -> None:
        """Thread-safe JSON file write."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


    def get_agent(self, agent_id: str) -> dict:
        path = self.data_dir / "agents" / f"{agent_id}.json"
        doc = self._read_json(path)
        if doc is None:
            raise KeyError(f"Agent '{agent_id}' not found in registry")
        return doc

    def get_all_agents(self) -> list[dict]:
        agents_dir = self.data_dir / "agents"
        agents = []
        for f in sorted(agents_dir.glob("*.json")):
            doc = self._read_json(f)
            if doc:
                agents.append(doc)
        return agents

    def upsert_agent(self, agent_doc: dict) -> None:
        agent_id = agent_doc["id"]
        path = self.data_dir / "agents" / f"{agent_id}.json"
        self._write_json(path, agent_doc)

    def get_agent_version(self, agent_id: str) -> str:
        doc = self.get_agent(agent_id)
        return doc.get("current_version", "1.0")


    def log_trace(self, trace: dict) -> None:
        run_id = trace["run_id"]
        agent_id = trace["agent"]
        trace_dir = self.data_dir / "traces" / run_id
        trace_dir.mkdir(parents=True, exist_ok=True)
        path = trace_dir / f"{agent_id}.json"
        self._write_json(path, trace)

    def get_traces_for_run(self, run_id: str) -> list[dict]:
        trace_dir = self.data_dir / "traces" / run_id
        if not trace_dir.exists():
            return []
        traces = []
        for f in sorted(trace_dir.glob("*.json")):
            doc = self._read_json(f)
            if doc:
                traces.append(doc)
        return traces

    def get_trace(self, run_id: str, agent_id: str) -> dict | None:
        path = self.data_dir / "traces" / run_id / f"{agent_id}.json"
        return self._read_json(path)


    def save_run_result(self, result: dict) -> None:
        run_id = result["run_id"]
        path = self.data_dir / "runs" / f"{run_id}.json"
        self._write_json(path, result)


    def save_candidate_prompt(self, agent_id: str, version: str, prompt: str) -> None:
        path = self.data_dir / "candidates" / f"{agent_id}_{version}.json"
        self._write_json(path, {"agent_id": agent_id, "version": version, "prompt": prompt})

    def get_candidate_prompt(self, agent_id: str, version: str) -> str:
        path = self.data_dir / "candidates" / f"{agent_id}_{version}.json"
        doc = self._read_json(path)
        if doc is None:
            raise KeyError(f"No candidate prompt for {agent_id} v{version}")
        return doc["prompt"]


    def save_shadow_output(self, run_id: str, agent_id: str, version: str, output: str) -> None:
        path = self.data_dir / "shadows" / f"{run_id}_{agent_id}_{version}.json"
        self._write_json(path, {
            "run_id": run_id,
            "agent_id": agent_id,
            "version": version,
            "output": output,
        })

    def get_shadow_output(self, run_id: str, agent_id: str, version: str) -> str:
        path = self.data_dir / "shadows" / f"{run_id}_{agent_id}_{version}.json"
        doc = self._read_json(path)
        if doc is None:
            raise KeyError(f"No shadow output for {agent_id} v{version} in run {run_id}")
        return doc["output"]


    def promote_agent(self, agent_id: str, version: str, new_prompt: str, eval_score: float) -> None:
        agent = self.get_agent(agent_id)
        agent["version_history"].append({
            "version": version,
            "system_prompt": new_prompt,
            "eval_score": eval_score,
            "promoted_at": datetime.now(timezone.utc).isoformat(),
        })
        agent["current_version"] = version
        agent["system_prompt"] = new_prompt
        agent["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.upsert_agent(agent)

    def reset_agent_to_version(self, agent_id: str, version: str) -> None:
        agent = self.get_agent(agent_id)
        # Find the target version in history
        target = None
        for v in agent["version_history"]:
            if v["version"] == version:
                target = v
                break
        if target is None:
            raise KeyError(f"Version {version} not found in history for {agent_id}")

        agent["current_version"] = version
        agent["system_prompt"] = target["system_prompt"]
        # Trim version history to only include versions up to and including target
        trimmed = []
        for v in agent["version_history"]:
            trimmed.append(v)
            if v["version"] == version:
                break
        agent["version_history"] = trimmed
        agent["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.upsert_agent(agent)


    def emit_event(self, event: dict) -> None:
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
        events_file = self.data_dir / "events" / "events.json"
        existing = self._read_json(events_file) or []
        existing.append(event)
        self._write_json(events_file, existing)

    def get_events_since(self, timestamp: str) -> list[dict]:
        events_file = self.data_dir / "events" / "events.json"
        all_events = self._read_json(events_file) or []
        if not timestamp:
            return all_events
        return [e for e in all_events if e.get("timestamp", "") > timestamp]


    def clear_traces_since(self, cutoff_minutes: int) -> None:
        cutoff = time.time() - (cutoff_minutes * 60)
        traces_dir = self.data_dir / "traces"
        if not traces_dir.exists():
            return
        for run_dir in traces_dir.iterdir():
            if run_dir.is_dir() and run_dir.stat().st_mtime > cutoff:
                for f in run_dir.glob("*.json"):
                    f.unlink()
                run_dir.rmdir()

    def clear_events(self) -> None:
        """Clear all events (for demo reset)."""
        events_file = self.data_dir / "events" / "events.json"
        self._write_json(events_file, [])


class CosmosRegistry(BaseRegistry):
    """
    Azure Cosmos DB registry implementation.

    Uses two containers:
    - agents (partition key: /id)
    - traces (partition key: /run_id)

    Plus additional containers for events, candidates, shadows, runs.
    """

    def __init__(self):
        from azure.cosmos import CosmosClient

        url = os.getenv("COSMOS_URL")
        key = os.getenv("COSMOS_KEY")
        if not url or not key:
            raise EnvironmentError("COSMOS_URL and COSMOS_KEY must be set for CosmosRegistry")

        client = CosmosClient(url, credential=key)
        db = client.get_database_client("metaswarm")

        self.agents_container = db.get_container_client("agents")
        self.traces_container = db.get_container_client("traces")
        self.events_container = db.get_container_client("events")
        self.candidates_container = db.get_container_client("candidates")
        self.shadows_container = db.get_container_client("shadows")
        self.runs_container = db.get_container_client("runs")


    def get_agent(self, agent_id: str) -> dict:
        return self.agents_container.read_item(item=agent_id, partition_key=agent_id)

    def get_all_agents(self) -> list[dict]:
        return list(self.agents_container.read_all_items())

    def upsert_agent(self, agent_doc: dict) -> None:
        self.agents_container.upsert_item(body=agent_doc)

    def get_agent_version(self, agent_id: str) -> str:
        doc = self.get_agent(agent_id)
        return doc.get("current_version", "1.0")


    def log_trace(self, trace: dict) -> None:
        self.traces_container.upsert_item(body=trace)

    def get_traces_for_run(self, run_id: str) -> list[dict]:
        query = "SELECT * FROM c WHERE c.run_id = @run_id ORDER BY c.timestamp"
        params = [{"name": "@run_id", "value": run_id}]
        return list(self.traces_container.query_items(query=query, parameters=params, partition_key=run_id))

    def get_trace(self, run_id: str, agent_id: str) -> dict | None:
        traces = self.get_traces_for_run(run_id)
        for t in traces:
            if t.get("agent") == agent_id:
                return t
        return None


    def save_run_result(self, result: dict) -> None:
        self.runs_container.upsert_item(body=result)


    def save_candidate_prompt(self, agent_id: str, version: str, prompt: str) -> None:
        doc = {"id": f"{agent_id}_{version}", "agent_id": agent_id, "version": version, "prompt": prompt}
        self.candidates_container.upsert_item(body=doc)

    def get_candidate_prompt(self, agent_id: str, version: str) -> str:
        doc_id = f"{agent_id}_{version}"
        doc = self.candidates_container.read_item(item=doc_id, partition_key=doc_id)
        return doc["prompt"]


    def save_shadow_output(self, run_id: str, agent_id: str, version: str, output: str) -> None:
        doc = {
            "id": f"{run_id}_{agent_id}_{version}",
            "run_id": run_id,
            "agent_id": agent_id,
            "version": version,
            "output": output,
        }
        self.shadows_container.upsert_item(body=doc)

    def get_shadow_output(self, run_id: str, agent_id: str, version: str) -> str:
        doc_id = f"{run_id}_{agent_id}_{version}"
        doc = self.shadows_container.read_item(item=doc_id, partition_key=doc_id)
        return doc["output"]


    def promote_agent(self, agent_id: str, version: str, new_prompt: str, eval_score: float) -> None:
        agent = self.get_agent(agent_id)
        agent["version_history"].append({
            "version": version,
            "system_prompt": new_prompt,
            "eval_score": eval_score,
            "promoted_at": datetime.now(timezone.utc).isoformat(),
        })
        agent["current_version"] = version
        agent["system_prompt"] = new_prompt
        agent["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.agents_container.upsert_item(body=agent)

    def reset_agent_to_version(self, agent_id: str, version: str) -> None:
        agent = self.get_agent(agent_id)
        target = None
        for v in agent["version_history"]:
            if v["version"] == version:
                target = v
                break
        if target is None:
            raise KeyError(f"Version {version} not found in history for {agent_id}")

        agent["current_version"] = version
        agent["system_prompt"] = target["system_prompt"]
        trimmed = []
        for v in agent["version_history"]:
            trimmed.append(v)
            if v["version"] == version:
                break
        agent["version_history"] = trimmed
        agent["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.agents_container.upsert_item(body=agent)


    def emit_event(self, event: dict) -> None:
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
        event["id"] = f"event_{int(time.time() * 1000)}"
        self.events_container.upsert_item(body=event)

    def get_events_since(self, timestamp: str) -> list[dict]:
        if not timestamp:
            query = "SELECT * FROM c ORDER BY c.timestamp"
            return list(self.events_container.query_items(query=query, enable_cross_partition_query=True))
        query = "SELECT * FROM c WHERE c.timestamp > @ts ORDER BY c.timestamp"
        params = [{"name": "@ts", "value": timestamp}]
        return list(self.events_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))


    def clear_traces_since(self, cutoff_minutes: int) -> None:
        cutoff = datetime.now(timezone.utc).isoformat()
        # For Cosmos DB, we'd query and delete — simplified for now
        query = "SELECT * FROM c WHERE c.timestamp > @cutoff"
        params = [{"name": "@cutoff", "value": cutoff}]
        items = list(self.traces_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
        for item in items:
            self.traces_container.delete_item(item=item["id"], partition_key=item["run_id"])


def get_registry() -> BaseRegistry:
    """
    Factory function — returns the appropriate registry based on REGISTRY_BACKEND env var.
    Defaults to LocalRegistry for immediate development.
    """
    backend = os.getenv("REGISTRY_BACKEND", "local").lower()
    if backend == "cosmos":
        return CosmosRegistry()
    return LocalRegistry()
