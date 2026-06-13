"""Seeds the registry with v1.0 agent documents.

Controller Agent v1.0 is deliberately naive to trigger evolution.
"""

from core.registry import get_registry


AGENT_SEEDS = [
    {
        "id": "spec_parser",
        "name": "Spec Parser",
        "current_version": "1.0",
        "system_prompt": (
            "You are an OpenAPI specification parser. "
            "Given an OpenAPI 3.0 JSON spec, extract all operationIds with their HTTP methods, "
            "paths, and summary descriptions. Output a structured list. "
            "Format each operation as: [METHOD] /path - operationId: summary"
        ),
        "version_history": [
            {
                "version": "1.0",
                "system_prompt": (
                    "You are an OpenAPI specification parser. "
                    "Given an OpenAPI 3.0 JSON spec, extract all operationIds with their HTTP methods, "
                    "paths, and summary descriptions. Output a structured list. "
                    "Format each operation as: [METHOD] /path - operationId: summary"
                ),
                "eval_score": None,
                "promoted_at": "2025-01-01T00:00:00Z",
            }
        ],
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "id": "route_builder",
        "name": "Route Builder",
        "current_version": "1.0",
        "system_prompt": (
            "You are an Express.js route scaffolding generator. "
            "Given a list of API operations with their HTTP methods and paths, "
            "generate a complete Express.js router file with route definitions. "
            "Use express.Router(). Each route should call a corresponding handler function. "
            "Import handlers from a separate controllers module. "
            "Export the router as default."
        ),
        "version_history": [
            {
                "version": "1.0",
                "system_prompt": (
                    "You are an Express.js route scaffolding generator. "
                    "Given a list of API operations with their HTTP methods and paths, "
                    "generate a complete Express.js router file with route definitions. "
                    "Use express.Router(). Each route should call a corresponding handler function. "
                    "Import handlers from a separate controllers module. "
                    "Export the router as default."
                ),
                "eval_score": None,
                "promoted_at": "2025-01-01T00:00:00Z",
            }
        ],
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        # Controller agent: v1.0 prompt deliberately omits spec-reading instructions
        # so the Refactor agent has to discover and add them.
        "id": "controller_agent",
        "name": "Controller Agent",
        "current_version": "1.0",
        "system_prompt": (
            "You are an Express.js controller generator. "
            "Given route scaffolding, generate handler functions for each route. "
            "Use Express.js with req, res parameters. "
            "Export all handlers as named functions."
        ),
        "version_history": [
            {
                "version": "1.0",
                "system_prompt": (
                    "You are an Express.js controller generator. "
                    "Given route scaffolding, generate handler functions for each route. "
                    "Use Express.js with req, res parameters. "
                    "Export all handlers as named functions."
                ),
                "eval_score": None,
                "promoted_at": "2025-01-01T00:00:00Z",
            }
        ],
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "id": "test_generator",
        "name": "Test Generator",
        "current_version": "1.0",
        "system_prompt": (
            "You are a Jest test generator for Express.js APIs. "
            "Given controller handler code, generate comprehensive Jest test cases. "
            "Use supertest for HTTP assertions. "
            "Test all success paths AND error paths (400, 404, 409 status codes). "
            "Each operationId should have at least 3 test cases: success, validation error, and edge case. "
            "Mock the database layer. Export test suites using describe/it blocks."
        ),
        "version_history": [
            {
                "version": "1.0",
                "system_prompt": (
                    "You are a Jest test generator for Express.js APIs. "
                    "Given controller handler code, generate comprehensive Jest test cases. "
                    "Use supertest for HTTP assertions. "
                    "Test all success paths AND error paths (400, 404, 409 status codes). "
                    "Each operationId should have at least 3 test cases: success, validation error, and edge case. "
                    "Mock the database layer. Export test suites using describe/it blocks."
                ),
                "eval_score": None,
                "promoted_at": "2025-01-01T00:00:00Z",
            }
        ],
        "updated_at": "2025-01-01T00:00:00Z",
    },
    {
        "id": "validator",
        "name": "Validator",
        "current_version": "1.0",
        "system_prompt": (
            "You are a code quality validator for Express.js REST APIs. "
            "Given handler code and its Jest tests, evaluate whether the handlers would pass the tests. "
            "Analyze each test case and determine if the handler implements the required logic. "
            "Do NOT run the tests — perform static analysis by reading the code. "
            "Count how many tests would pass vs fail based on the handler implementation. "
            "\n\nRespond ONLY with this JSON, nothing else:\n"
            '{"passed": N, "total": N, "score": N, "failures": ["brief description of each failing test"]}'
        ),
        "version_history": [
            {
                "version": "1.0",
                "system_prompt": (
                    "You are a code quality validator for Express.js REST APIs. "
                    "Given handler code and its Jest tests, evaluate whether the handlers would pass the tests. "
                    "Analyze each test case and determine if the handler implements the required logic. "
                    "Do NOT run the tests — perform static analysis by reading the code. "
                    "Count how many tests would pass vs fail based on the handler implementation. "
                    "\n\nRespond ONLY with this JSON, nothing else:\n"
                    '{"passed": N, "total": N, "score": N, "failures": ["brief description of each failing test"]}'
                ),
                "eval_score": None,
                "promoted_at": "2025-01-01T00:00:00Z",
            }
        ],
        "updated_at": "2025-01-01T00:00:00Z",
    },
]


def seed():
    """Write all v1.0 agent documents to the registry."""
    registry = get_registry()

    print("Seeding registry with v1.0 agent documents...")
    for agent_doc in AGENT_SEEDS:
        registry.upsert_agent(agent_doc)
        print(f"  ✓ {agent_doc['name']} (v{agent_doc['current_version']})")

    print(f"\nSeeded {len(AGENT_SEEDS)} agents.")
    print("Controller Agent v1.0 prompt is deliberately naive — evolution will fix it.")


if __name__ == "__main__":
    seed()
