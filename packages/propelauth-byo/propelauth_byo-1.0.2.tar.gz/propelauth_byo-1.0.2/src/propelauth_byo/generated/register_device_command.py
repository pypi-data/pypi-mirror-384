"""Auto-generated from TypeScript type: RegisterDeviceCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class RegisterDeviceCommand:
    signed_device_challenge: str
    remember_device: bool
    session_token: Optional[str] = None
    session_id: Optional[str] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["signedDeviceChallenge"] = self.signed_device_challenge
        data["rememberDevice"] = self.remember_device
        if self.session_token is not None:
            data["sessionToken"] = self.session_token
        if self.session_id is not None:
            data["sessionId"] = self.session_id
        if self.request_url is not None:
            data["requestUrl"] = self.request_url
        if self.request_method is not None:
            data["requestMethod"] = self.request_method
        if self.user_agent is not None:
            data["userAgent"] = self.user_agent
        if self.ip_address is not None:
            data["ipAddress"] = self.ip_address
        return data