"""Auto-generated from TypeScript type: CreateSessionResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class CreateSessionResponse:
    session_id: str
    session_token: str
    expires_at: int
    new_device_detected: Optional[bool] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        data["sessionToken"] = self.session_token
        data["expiresAt"] = self.expires_at
        if self.new_device_detected is not None:
            data["newDeviceDetected"] = self.new_device_detected
        return data