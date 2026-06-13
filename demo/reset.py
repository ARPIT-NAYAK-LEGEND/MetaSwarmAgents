"""Resets the system to a clean v1.0 state for a fresh demo run."""

from core.registry import get_registry


def reset_for_demo():
    """Reset MetaSwarm to initial state for a fresh demo run."""
    registry = get_registry()

    print("Resetting MetaSwarm for demo...")

    # Reset Controller Agent back to v1.0
    try:
        registry.reset_agent_to_version("controller_agent", "1.0")
        print("  ✓ Controller Agent reset to v1.0")
    except KeyError as e:
        print(f"  ⚠ Could not reset controller_agent: {e}")
        print("    Run 'python -m demo.seed_registry' first.")
        return

    # Clear recent traces
    registry.clear_traces_since(cutoff_minutes=60)
    print("  ✓ Cleared recent traces (last 60 minutes)")

    # Clear events
    if hasattr(registry, "clear_events"):
        registry.clear_events()
        print("  ✓ Cleared all events")

    # Emit reset event
    registry.emit_event({
        "type": "reset",
        "message": "Demo reset to initial state — Controller Agent is v1.0",
    })
    print("  ✓ Emitted reset event")

    print("\n✅ Ready. Controller Agent is v1.0. Go.")


if __name__ == "__main__":
    reset_for_demo()
