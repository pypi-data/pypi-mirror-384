"""Auto-generated from TypeScript type: StartPasskeyRegistrationResponse"""
from dataclasses import dataclass
from typing import Dict, Any
from .serde_json.json_value import JsonValue


@dataclass
class StartPasskeyRegistrationResponse:
    registration_options: JsonValue

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["registrationOptions"] = self.registration_options
        return data