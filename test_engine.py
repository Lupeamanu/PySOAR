"""
Test script for PySOAR playbook engine with integrations
"""
from src.core.playbook_engine import PlaybookEngine
from src.core.integration_manager import IntegrationManager
import json


def main():
    print("=" * 70)
    print("PySOAR - Playbook Engine Test with API Integrations")
    print("=" * 70)
    
    # Initialize integration manager
    print("\n[1] Loading integrations...")
    integration_manager = IntegrationManager('config/integrations.yaml')
    print(f"Loaded integrations: {integration_manager.list_integrations()}")
    
    # Initialize engine with integration manager
    print("\n[2] Initializing playbook engine...")
    engine = PlaybookEngine(integration_manager=integration_manager)
    
    # Load the IP investigation playbook
    print("\n[3] Loading playbook...")
    playbook = engine.load_playbook('config/playbooks/ip_investigation.yaml')
    print(f"Loaded: {playbook.name}")
    print(f"Description: {playbook.description}")
    print(f"Actions: {len(playbook.actions)}")
    
    # Test 1: Internal IP (should be low risk)
    print("\n" + "=" * 70)
    print("TEST 1: Investigating Internal IP")
    print("=" * 70)
    result1 = engine.execute(playbook, inputs={'ip_address': '192.168.1.100'})
    print(f"\n✓ Status: {result1['status']}")
    print(f"✓ Duration: {result1['duration_seconds']:.2f}s")
    print(f"✓ Risk Score: {result1['context'].get('risk_score', 'N/A')}")
    print(f"✓ Recommended Action: {result1['context'].get('recommended_action', 'N/A')}")
    
    # Test 2: External IP (should be higher risk)
    print("\n" + "=" * 70)
    print("TEST 2: Investigating External IP")
    print("=" * 70)
    result2 = engine.execute(playbook, inputs={'ip_address': '8.8.8.8'})
    print(f"\n✓ Status: {result2['status']}")
    print(f"✓ Duration: {result2['duration_seconds']:.2f}s")
    print(f"✓ Risk Score: {result2['context'].get('risk_score', 'N/A')}")
    print(f"✓ Recommended Action: {result2['context'].get('recommended_action', 'N/A')}")
    
    # Show VirusTotal results
    print("\n" + "=" * 70)
    print("VirusTotal Analysis Details:")
    print("=" * 70)
    vt_result = result2['context'].get('vt_result', {})
    if vt_result.get('mock_data'):
        print("⚠️  Using mock data (no API key configured)")
        vt_data = vt_result.get('data', {})
    else:
        vt_data = vt_result
    
    print(json.dumps(vt_data, indent=2))
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()