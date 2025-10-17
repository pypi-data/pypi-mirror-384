"""Auto-generated from TypeScript type: CreateSessionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .serde_json.json_value import JsonValue
from .device_registration import DeviceRegistration


@dataclass
class CreateSessionCommand:
    user_id: str
    tags: Optional[List[str]] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Optional[JsonValue] = None
    device_registration: Optional[DeviceRegistration] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        if self.tags is not None:
            data["tags"] = self.tags
        if self.user_agent is not None:
            data["userAgent"] = self.user_agent
        if self.ip_address is not None:
            data["ipAddress"] = self.ip_address
        if self.metadata is not None:
            data["metadata"] = self.metadata
        if self.device_registration is not None:
            data["deviceRegistration"] = self.device_registration._to_request()
        return data