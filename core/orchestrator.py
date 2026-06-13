"""Pipeline runner: executes the worker swarm and, on failure,
the meta-swarm evolution loop.
"""

import json
import re
import sys
import time
import uuid
import asyncio
from datetime import datetime, timezone

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.registry import BaseRegistry, get_registry
from core.rubric import FAILURE_THRESHOLD
from agents.workers.spec_parser import build_spec_parser
from agents.workers.route_builder import build_route_builder
from agents.workers.controller_agent import build_controller_agent
from agents.workers.test_generator import build_test_generator
from agents.workers.validator import build_validator
from agents.meta.observer import run_observer
from agents.meta.bottleneck import run_bottleneck
from agents.meta.refactor import run_refactor
from agents.meta.shadow import run_shadow
from agents.meta.eval_agent import run_eval
from agents.meta.promotion import run_promotion


class Orchestrator:
    """
    Main pipeline runner.

    Manages the worker swarm pipeline and the meta-swarm evolution loop.
    """

    def __init__(self, registry: BaseRegistry):
        self.registry = registry

    # -- Worker Swarm Pipeline --

    def run_worker_pipeline(self, task: dict) -> dict:
        """
        Run the 5-agent worker pipeline in sequence.

        Args:
            task: Dict with "spec" key containing the OpenAPI spec.

        Returns:
            Dict with run_id, score, handlers, tests, and validation result.
        """
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        spec_json = task["spec"] if isinstance(task["spec"], str) else json.dumps(task["spec"], indent=2)

        self.registry.emit_event({
            "type": "run_started",
            "run_id": run_id,
            "message": "Worker swarm pipeline started",
        })

        # Step 1: Spec Parser
        print("  [1/5] Spec Parser — extracting operations...")
        spec_agent = build_spec_parser()
        parsed_spec = self._call_agent(
            spec_agent,
            f"Parse this OpenAPI spec and extract all operationIds with their HTTP methods, paths, and descriptions:\n\n{spec_json}",
            agent_id="spec_parser",
            run_id=run_id,
        )
        print(f"        ✓ Extracted operations ({len(parsed_spec)} chars)")

        # Step 2: Route Builder
        print("  [2/5] Route Builder — generating Express.js scaffolding...")
        route_agent = build_route_builder()
        routes = self._call_agent(
            route_agent,
            f"Generate Express.js route scaffolding for these operations:\n\n{parsed_spec}",
            agent_id="route_builder",
            run_id=run_id,
        )
        print(f"        ✓ Generated route scaffolding ({len(routes)} chars)")

        # Step 3: Controller Agent (the one that v1.0 fails on)
        print("  [3/5] Controller Agent — generating handlers...")
        controller = build_controller_agent(self.registry)
        controller_version = self.registry.get_agent_version("controller_agent")
        handlers = self._call_agent(
            controller,
            f"Spec:\n{spec_json}\n\nRoute scaffolding:\n{routes}\n\nGenerate handler functions for each route.",
            agent_id="controller_agent",
            run_id=run_id,
        )
        print(f"        ✓ Generated handlers (v{controller_version}, {len(handlers)} chars)")

        # Step 4: Test Generator
        print("  [4/5] Test Generator — writing Jest tests...")
        test_agent = build_test_generator()
        tests = self._call_agent(
            test_agent,
            f"Write Jest tests for these Express.js handler functions:\n\n{handlers}",
            agent_id="test_generator",
            run_id=run_id,
        )
        print(f"        ✓ Generated tests ({len(tests)} chars)")

        # Step 5: Validator
        print("  [5/5] Validator — evaluating quality...")
        validator = build_validator()
        result_str = self._call_agent(
            validator,
            f"Handlers:\n{handlers}\n\nTests:\n{tests}\n\n"
            f"Evaluate whether these handlers would pass these tests and return JSON: "
            f'{{"passed": N, "total": N, "score": N, "failures": ["description"]}}',
            agent_id="validator",
            run_id=run_id,
        )
        print(f"        ✓ Validation complete")

        # Parse validation result
        result = self._parse_validator_output(result_str)
        result["run_id"] = run_id
        result["handlers"] = handlers
        result["tests"] = tests
        result["controller_version"] = controller_version

        # Save run result
        self.registry.save_run_result(result)

        # Emit result event
        status = "passed" if result.get("score", 0) >= FAILURE_THRESHOLD else "failed"
        self.registry.emit_event({
            "type": "run_complete",
            "run_id": run_id,
            "score": result.get("score", 0),
            "passed": result.get("passed", 0),
            "total": result.get("total", 0),
            "status": status,
        })

        return result

    def _call_agent(self, agent: AssistantAgent, message: str, *, agent_id: str, run_id: str) -> str:
        """
        Call an agent with a message and return its response.

        Traces the I/O to the registry for the Observer agent.
        """
        from core.tracer import call_traced_agent_sync
        return call_traced_agent_sync(
            agent, message,
            agent_id=agent_id,
            registry=self.registry,
            run_id=run_id,
        )

    def _parse_validator_output(self, raw: str) -> dict:
        """
        Parse the Validator's JSON output.

        Handles cases where the LLM wraps JSON in markdown code fences
        or includes extra text.
        """
        # Try to extract JSON from the response
        cleaned = raw.strip()

        # Strip markdown code fences
        if "```" in cleaned:
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)```', cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(1).strip()

        # Try to find JSON object in the text
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find a JSON object anywhere in the string
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        # Fallback: return a failure result
        print(f"  ⚠ Could not parse validator output, using fallback scores")
        return {"passed": 0, "total": 17, "score": 0, "failures": ["Could not parse validator output"]}

    # -- Full Demo Pipeline --

    def run_full_demo(self, task: dict) -> dict:
        """
        Run the complete MetaSwarm demo:
        1. Worker swarm (will fail with v1.0)
        2. Meta-swarm (observe → diagnose → fix → shadow → eval → promote)
        3. Re-run worker swarm (succeeds with v2.0)
        """
        spec_str = task["spec"] if isinstance(task["spec"], str) else json.dumps(task["spec"], indent=2)

        # Phase 1: worker swarm (expected to fail with v1.0)
        print("\n" + "=" * 60)
        print("PHASE 1: Running worker swarm pipeline...")
        print("=" * 60)

        worker_result = self.run_worker_pipeline(task)
        score = worker_result.get("score", 0)

        print(f"\n  Result: score={score}/100, "
              f"passed={worker_result.get('passed', 0)}/{worker_result.get('total', 0)}")

        if score >= FAILURE_THRESHOLD:
            print(f"\n  ✓ Task succeeded — no evolution needed.")
            return worker_result

        print(f"\n  ✗ Task FAILED (score: {score}/100) — triggering meta-swarm")
        run_id = worker_result["run_id"]

        # Phase 2: meta-swarm evolution
        print("\n" + "=" * 60)
        print("PHASE 2: Meta-swarm evolution")
        print("=" * 60)

        # Observer
        print("\n  [1/6] Observer — scoring all agents...")
        time.sleep(2)
        scores = run_observer(self.registry, run_id)
        self.registry.emit_event({
            "type": "observer_complete",
            "run_id": run_id,
            "scores": scores["scores"],
            "analysis": scores.get("analysis", {}),
        })
        for agent_name, agent_score in scores["scores"].items():
            analysis = scores.get("analysis", {}).get(agent_name, "")
            print(f"        {agent_name}: {agent_score}/100 — {analysis}")

        # Bottleneck
        print("\n  [2/6] Bottleneck — identifying root cause...")
        time.sleep(2)
        bottleneck = run_bottleneck(self.registry, run_id, scores)
        self.registry.emit_event({
            "type": "bottleneck_found",
            "run_id": run_id,
            "agent": bottleneck["failing_agent"],
            "root_cause": bottleneck["root_cause"],
            "missing": bottleneck["missing_instruction"],
        })
        print(f"        Failing agent: {bottleneck['failing_agent']} (v{bottleneck.get('version', '1.0')})")
        print(f"        Root cause: {bottleneck['root_cause']}")
        print(f"        Missing: {bottleneck['missing_instruction']}")

        # Refactor
        print(f"\n  [3/6] Refactor — rewriting {bottleneck['failing_agent']}'s prompt...")
        time.sleep(1)
        new_prompt = run_refactor(self.registry, bottleneck)
        self.registry.emit_event({
            "type": "refactor_complete",
            "run_id": run_id,
            "agent": bottleneck["failing_agent"],
            "new_prompt_preview": new_prompt[:200],
        })
        print(f"        New prompt: {new_prompt[:150]}...")

        # Shadow
        print("\n  [4/6] Shadow — running A/B test with v2.0...")
        time.sleep(1)
        shadow_output = run_shadow(self.registry, run_id)
        self.registry.emit_event({
            "type": "shadow_complete",
            "run_id": run_id,
            "agent": bottleneck["failing_agent"],
        })
        print(f"        Shadow output: {len(shadow_output)} chars generated")

        # Eval
        print("\n  [5/6] Eval — comparing v1.0 vs v2.0...")
        time.sleep(3)
        eval_result = run_eval(self.registry, run_id, spec_str)
        self.registry.emit_event({
            "type": "eval_complete",
            "run_id": run_id,
            "v1_score": eval_result["v1"]["total"],
            "v2_score": eval_result["v2"]["total"],
            "winner": eval_result["winner"],
            "improvement": eval_result.get("improvement_summary", ""),
        })
        print(f"        v1.0: {eval_result['v1']['total']}/100")
        print(f"        v2.0: {eval_result['v2']['total']}/100")
        print(f"        Winner: {eval_result['winner']}")

        # Promotion
        print("\n  [6/6] Promotion — deciding whether to promote v2.0...")
        time.sleep(1.5)
        promoted = run_promotion(self.registry, eval_result, bottleneck["failing_agent"])

        if not promoted:
            print("\n  ✗ Promotion threshold not met. Meta-swarm could not fix the issue.")
            return worker_result

        # Phase 3: re-run with evolved agent
        print("\n" + "=" * 60)
        print("PHASE 3: Re-running worker swarm with evolved agents...")
        print("=" * 60)

        time.sleep(2)
        final_result = self.run_worker_pipeline(task)
        final_score = final_result.get("score", 0)

        print(f"\n  Result: score={final_score}/100, "
              f"passed={final_result.get('passed', 0)}/{final_result.get('total', 0)}")

        if final_score >= FAILURE_THRESHOLD:
            print(f"\n  ✓ SUCCESS! The swarm evolved itself and now passes.")
        else:
            print(f"\n  ⚠ Score improved but still below threshold. May need another evolution cycle.")

        return final_result




def main():
    """CLI entry point for running the orchestrator."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="MetaSwarm Orchestrator")
    parser.add_argument("--full", action="store_true", help="Run full demo (fail → evolve → succeed)")
    parser.add_argument("--spec", type=str, default=None, help="Path to spec.json (default: demo/spec.json)")
    args = parser.parse_args()

    # Load spec
    spec_path = args.spec or str(Path(__file__).resolve().parent.parent / "demo" / "spec.json")
    with open(spec_path, "r") as f:
        spec = json.load(f)

    task = {"spec": spec}

    # Initialize
    registry = get_registry()
    orchestrator = Orchestrator(registry)

    if args.full:
        print("\n🚀 MetaSwarm — Full Demo Pipeline")
        print("=" * 60)
        result = orchestrator.run_full_demo(task)
    else:
        print("\n🔧 MetaSwarm — Worker Pipeline Only")
        print("=" * 60)
        result = orchestrator.run_worker_pipeline(task)

    print("\n" + "=" * 60)
    print(f"Final score: {result.get('score', 'N/A')}/100")
    print(f"Run ID: {result.get('run_id', 'N/A')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
