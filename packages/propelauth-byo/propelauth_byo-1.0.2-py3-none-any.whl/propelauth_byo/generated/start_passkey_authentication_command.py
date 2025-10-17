"""Auto-generated from TypeScript type: StartPasskeyAuthenticationCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class StartPasskeyAuthenticationCommand:
    user_id: str
    additional_allowed_origin: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        if self.additional_allowed_origin is not None:
            data["additionalAllowedOrigin"] = self.additional_allowed_origin
        return data