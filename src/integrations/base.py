""" Base integration class for PySOAR """

from abc import ABC, abstractmethod
from typing import Dict, Any
import requests


class BaseIntegration(ABC):
    """ Base class for all integrations """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.name = config.get("name", self.__class__.__name__)
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")


    @abstractmethod
    def get_available_actions(self) -> list:
        """ Return list of available action names for this integration """
        pass


    @abstractmethod
    def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """ Execute a specific action with given parameters """
        pass


    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """ Helper method to make HTTP requests """
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {}
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    