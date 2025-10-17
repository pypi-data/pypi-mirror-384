"""Auto-generated from TypeScript type: CreateScimConnectionResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CreateScimConnectionResponse:
    connection_id: str
    scim_api_key: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["scimApiKey"] = self.scim_api_key
        return data