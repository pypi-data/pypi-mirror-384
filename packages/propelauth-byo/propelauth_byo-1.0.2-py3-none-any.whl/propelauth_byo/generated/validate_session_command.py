"""Auto-generated from TypeScript type: ValidateSessionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .device_verification import DeviceVerification


@dataclass
class ValidateSessionCommand:
    session_token: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    required_tags: Optional[List[str]] = None
    device_verification: Optional[DeviceVerification] = None
    ignore_device_for_verification: Optional[bool] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.session_token is not None:
            data["sessionToken"] = self.session_token
        if self.user_agent is not None:
            data["userAgent"] = self.user_agent
        if self.ip_address is not None:
            data["ipAddress"] = self.ip_address
        if self.required_tags is not None:
            data["requiredTags"] = self.required_tags
        if self.device_verification is not None:
            data["deviceVerification"] = self.device_verification._to_request()
        if self.ignore_device_for_verification is not None:
            data["ignoreDeviceForVerification"] = self.ignore_device_for_verification
        return data