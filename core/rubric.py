"""Eval rubric and scoring constants for version comparison."""

EVAL_RUBRIC_PROMPT = """You are a deterministic code quality scorer.
Given an OpenAPI spec and two versions of controller code, score each on four dimensions (0-25 each).

Dimensions:
- logic_completeness: Do handlers implement the operation logic described in each operationId summary? (0=all stubs, 25=all implemented)
- route_coverage: What fraction of operationIds have handler functions? (0=none, 25=all 5)
- error_handling: Are 400/404/409/500 errors handled appropriately per spec requirements? (0=none, 25=comprehensive)
- spec_adherence: Do responses match the shapes implied by each operation summary? (0=no match, 25=full match)

You MUST respond with ONLY this JSON, nothing else:
{
  "v1": {"logic_completeness": N, "route_coverage": N, "error_handling": N, "spec_adherence": N, "total": N},
  "v2": {"logic_completeness": N, "route_coverage": N, "error_handling": N, "spec_adherence": N, "total": N},
  "winner": "v1" or "v2",
  "improvement_summary": "One sentence."
}"""


# Scoring constants
PROMOTION_THRESHOLD = 70  # v2.0 must score >= 70 to be promoted
FAILURE_THRESHOLD = 30    # A run scoring below this triggers the meta-swarm

# Dimension weights (equal for now — each max 25, total max 100)
DIMENSIONS = [
    "logic_completeness",
    "route_coverage",
    "error_handling",
    "spec_adherence",
]
