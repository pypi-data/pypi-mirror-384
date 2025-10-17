"""Auto-generated from TypeScript type: PasskeyInfo"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PasskeyInfo:
    credential_id: str
    display_name: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["credentialId"] = self.credential_id
        if self.display_name is not None:
            data["displayName"] = self.display_name
        return data