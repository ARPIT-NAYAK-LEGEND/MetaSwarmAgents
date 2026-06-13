"""Promotes a failing agent to v2.0 if the eval score clears the threshold."""

from core.registry import BaseRegistry
from core.rubric import PROMOTION_THRESHOLD


def run_promotion(registry: BaseRegistry, eval_result: dict, failing_agent: str) -> bool:
    """
    Promote the failing agent to v2.0 if its eval score exceeds the threshold.

    Returns True if promoted, False if rejected.
    """
    v2_score = eval_result["v2"]["total"]

    if v2_score < PROMOTION_THRESHOLD:
        print(f"  ✗ v2.0 scored {v2_score} — below threshold {PROMOTION_THRESHOLD}. Not promoting.")

        registry.emit_event({
            "type": "promotion_rejected",
            "agent_id": failing_agent,
            "score": v2_score,
            "threshold": PROMOTION_THRESHOLD,
            "reason": f"Score {v2_score} below threshold {PROMOTION_THRESHOLD}",
        })

        return False

    new_prompt = registry.get_candidate_prompt(failing_agent, "2.0")
    registry.promote_agent(failing_agent, "2.0", new_prompt, v2_score)

    registry.emit_event({
        "type": "promotion",
        "agent_id": failing_agent,
        "old_version": "1.0",
        "new_version": "2.0",
        "score": v2_score,
    })

    print(f"  ✓ Promoted {failing_agent} to v2.0 (score: {v2_score}/100)")
    return True
