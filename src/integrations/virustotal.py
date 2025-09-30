""" VirusTotal integration for PySOAR """

from typing import Dict, Any
from .base import BaseIntegration


class VirusTotalIntegration(BaseIntegration):
    """ Integration with VirusTotal API """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.base_url = "https://www.virustotal.com/api/v3"


    def get_available_actions(self) -> list:
        return ["check_ip", "check_domain", "check_hash"]


    def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """ Execute VirusTotal action """
        if action_name == "check_ip":
            return self.check_ip(parameters.get("ip")) # type: ignore
        elif action_name == "check_domain":
            return self.check_domain(parameters.get("domain")) # type: ignore
        elif action_name == "check_hash":
            return self.check_hash(parameters.get("hash")) # type: ignore
        else:
            return {"success": False, "error": f"Unknown action: {action_name}"}


    def check_ip(self, ip: str) -> Dict[str, Any]:
        """ Check IP address reputation """
        if not self.api_key:
            return {
                "success": False,
                "error": "VirusTotal API key not configured",
                "mock_data": True,
                "data": self._mock_ip_response(ip)
            }

        url = f"{self.base_url}/ip_addresses/{ip}"
        headers = {"x-apikey": self.api_key}

        response = self._make_request('GET', url, headers=headers)

        if response["success"]:
            # Parse the response
            data = response.get("data", {})
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})

            return {
                "success": True,
                "ip": ip,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
                "reputation": stats.get("reputation", 0)
            }

        return response


    def check_domain(self, domain: str) -> Dict[str, Any]:
        """ Check domain reputation """
        if not self.api_key:
            return {
                "success": False,
                "error": "VirusTotal API key not configured",
                "mock_data": True,
                "data": self._mock_domain_response(domain)
            }

        url = f"{self.base_url}/domains/{domain}"
        headers = {"x-apikey": self.api_key}

        response = self._make_request("GET", url, headers=headers)

        if response["success"]:
            data = response.get("data", {})
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})

            return {
                'success': True,
                'domain': domain,
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'harmless': stats.get('harmless', 0),
                'undetected': stats.get('undetected', 0)
            }

        return response


    def check_hash(self, file_hash: set) -> Dict[str, Any]:
        """ Check file hash reputation """
        if not self.api_key:
            return {
                "success": False,
                "error": "VirusTotal API key not configured",
                "mock_data": True,
                "data": self._mock_hash_response(file_hash) # type: ignore
            }

        url = f"{self.base_url}/files/{file_hash}"
        headers = {"x-apikey": self.api_key}

        response = self._make_request("GET", url, headers=headers)

        if response["success"]:
            data = response.get("data", {})
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})

            return {
                "success": True,
                "hash": file_hash,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0)
            }

        return response


    def _mock_ip_response(self, ip: str) -> Dict[str, Any]:
        """ Return mock data for testing without API key """
        # Simulate different responses based on IP
        if ip.startswith("192.168") or ip.startswith("10."):
            malicious = 0
            reputation = 100
        else:
            malicious = 5
            reputation = -20

        return {
            "ip": ip,
            "malicious": malicious,
            "suspicious": 2,
            "harmless": 50,
            "undetected": 20,
            "reputation": reputation
        }


    def _mock_domain_response(self, domain: str) -> Dict[str, Any]:
        """ Return mock data for testing without API key """
        # Simulate suspicious domains
        suspicious_keywords = ["malware", "phishing", "suspicious", "hack"]
        malicious = 10 if any(kw in domain.lower() for kw in suspicious_keywords) else 0

        return {
            "domain": domain,
            "malicious": malicious,
            "suspicious": 3 if malicious > 0 else 0,
            "harmless": 40,
            "undetected": 15
        }


    def _mock_hash_response(self, file_hash: str) -> Dict[str, Any]:
        """ Return mock data for testing without API key """
        # Simulate based on hash characteristics
        malicious = 15 if len(file_hash) == 32 else 2

        return {
            "hash": file_hash,
            "malicious": malicious,
            "suspicious": 5,
            "harmless": 35,
            "undetected": 10
        }
        