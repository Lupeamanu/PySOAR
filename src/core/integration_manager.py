""" Integration manager for PySOAR. Handles loading and executing integrations """

import yaml
from typing import Dict, Any
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from integrations.virustotal import VirusTotalIntegration


class IntegrationManager:
    """ Manages all security tool integrations """

    def __init__(self, config_path: str = None): # type: ignore
        self.integrations = {}
        if config_path:
            self.load_config(config_path)


    def load_config(self, config_path: str):
        """ Load integration configuration from YAML file """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        integrations_config = config.get("integrations", {})

        # Initialize each enabled integration
        for name, integration_config in integrations_config.items():
            if integration_config.get("enabled", False):
                self._initialize_integration(name, integration_config)


    def _initialize_integration(self, name: str, config: Dict[str, Any]):
        """ Initialize a specific integration """
        config["name"] = name

        # Map integration names to classes
        integration_classes = {
            "virustotal": VirusTotalIntegration,
            # Add more here once implemented
        }

        integration_class = integration_classes.get(name)
        if integration_class:
            self.integrations[name] = integration_class(config)
            print(f"Loaded integration: '{name}'")
        else:
            print(f"Warning: Unknown integration: '{name}'")


    def execute_action(self, integration_name: str, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """ Execute an action on a specific integration """
        integration = self.integrations.get(integration_name)

        if not integration:
            return {
                "success": False,
                "error": f"Integration '{integration_name}' not found or not enabled"
            }

        return integration.execute_action(action_name, parameters)


    def get_integration(self, name: str):
        """ Get a specific integration """
        return self.integrations.get(name)


    def list_integrations(self) -> list:
        """ List all loaded integrations """
        return list(self.integrations.keys())