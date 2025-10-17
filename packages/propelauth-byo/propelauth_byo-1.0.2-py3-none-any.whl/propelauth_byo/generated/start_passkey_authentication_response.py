"""Auto-generated from TypeScript type: StartPasskeyAuthenticationResponse"""
from dataclasses import dataclass
from typing import Dict, Any
from .serde_json.json_value import JsonValue


@dataclass
class StartPasskeyAuthenticationResponse:
    authentication_options: JsonValue

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["authenticationOptions"] = self.authentication_options
        return data