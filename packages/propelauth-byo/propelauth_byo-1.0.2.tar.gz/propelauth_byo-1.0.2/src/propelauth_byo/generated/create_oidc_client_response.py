"""Auto-generated from TypeScript type: CreateOidcClientResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CreateOidcClientResponse:
    client_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["clientId"] = self.client_id
        return data