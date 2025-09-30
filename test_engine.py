""" Quick test script for PySOAR playbook engine """

from src.core.playbook_engine import PlaybookEngine
import json


def main():
    # Initialize the engine
    engine = PlaybookEngine()

    # Load the playbook
    print("Loading playbook...")
    playbook = engine.load_playbook("config/playbooks/simple_test.yaml")
    print(f"Loaded: {playbook.name}")
    print(f"Description: {playbook.description}")
    print(f"Actions: {len(playbook.actions)}\n")

    # Test with an internal IP
    print("=" * 60)
    print("TEST 1: Internal IP")
    print("=" * 60)
    result1 = engine.execute(playbook, inputs={"ip_address": "192.168.1.100"})
    print(f"\nStatus: {result1['status']}")
    print(f"Duration: {result1['duration_seconds']:.2f}s")

    # Test with an external IP
    print("\n" + "=" * 60)
    print("TEST 2: External IP")
    print("=" * 60)
    result2 = engine.execute(playbook, inputs={"ip_address": "8.8.8.8"})
    print(f"\nStatus: {result2['status']}")
    print(f"Duration: {result2['duration_seconds']:.2f}s")

    # Show the final context
    print("\n" + "=" * 60)
    print("Final Context Variables:")
    print("=" * 60)
    print(json.dumps(result2["context"], indent=2))


if __name__ == "__main__":
    main()