"""Auto-generated from TypeScript type: DeregisterPasskeyCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DeregisterPasskeyCommand:
    user_id: str
    credential_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        data["credentialId"] = self.credential_id
        return data