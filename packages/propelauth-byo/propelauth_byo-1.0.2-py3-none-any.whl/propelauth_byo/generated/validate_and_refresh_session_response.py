"""Auto-generated from TypeScript type: ValidateAndRefreshSessionResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .serde_json.json_value import JsonValue


@dataclass
class ValidateAndRefreshSessionResponse:
    session_id: str
    user_id: str
    created_at: int
    expires_at: int
    has_device_registered: bool
    tags: Optional[List[str]] = None
    metadata: Optional[JsonValue] = None
    new_session_token: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        data["userId"] = self.user_id
        data["createdAt"] = self.created_at
        data["expiresAt"] = self.expires_at
        data["hasDeviceRegistered"] = self.has_device_registered
        if self.tags is not None:
            data["tags"] = self.tags
        if self.metadata is not None:
            data["metadata"] = self.metadata
        if self.new_session_token is not None:
            data["newSessionToken"] = self.new_session_token
        return data