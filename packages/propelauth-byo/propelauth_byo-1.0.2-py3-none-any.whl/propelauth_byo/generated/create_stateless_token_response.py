"""Auto-generated from TypeScript type: CreateStatelessTokenResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CreateStatelessTokenResponse:
    stateless_token: str
    expires_at: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["statelessToken"] = self.stateless_token
        data["expiresAt"] = self.expires_at
        return data