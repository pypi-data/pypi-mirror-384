"""Auto-generated from TypeScript type: FinishPasskeyAuthenticationCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .serde_json.json_value import JsonValue


@dataclass
class FinishPasskeyAuthenticationCommand:
    user_id: str
    public_key: JsonValue
    additional_allowed_origin: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        data["publicKey"] = self.public_key
        if self.additional_allowed_origin is not None:
            data["additionalAllowedOrigin"] = self.additional_allowed_origin
        return data