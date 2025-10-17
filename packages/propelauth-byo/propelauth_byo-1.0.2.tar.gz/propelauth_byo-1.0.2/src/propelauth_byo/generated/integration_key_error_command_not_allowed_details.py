"""Auto-generated from TypeScript type: IntegrationKeyErrorCommandNotAllowedDetails"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class IntegrationKeyErrorCommandNotAllowedDetails:
    command_name: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["command_name"] = self.command_name
        return data