"""Auto-generated from TypeScript type: SessionInfo"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .device_info import DeviceInfo
from .serde_json.json_value import JsonValue


@dataclass
class SessionInfo:
    session_id: str
    created_at: int
    expires_at: int
    last_activity_at: int
    device: DeviceInfo
    ip_address: Optional[str] = None
    session_tags: Optional[List[str]] = None
    metadata: Optional[JsonValue] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        data["createdAt"] = self.created_at
        data["expiresAt"] = self.expires_at
        data["lastActivityAt"] = self.last_activity_at
        data["device"] = self.device._to_request()
        if self.ip_address is not None:
            data["ipAddress"] = self.ip_address
        if self.session_tags is not None:
            data["sessionTags"] = self.session_tags
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return data