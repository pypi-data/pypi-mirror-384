"""Auto-generated from TypeScript type: DeviceRegistration"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class DeviceRegistration:
    signed_device_challenge: str
    remember_device: Optional[bool] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["signedDeviceChallenge"] = self.signed_device_challenge
        if self.remember_device is not None:
            data["rememberDevice"] = self.remember_device
        if self.request_url is not None:
            data["requestUrl"] = self.request_url
        if self.request_method is not None:
            data["requestMethod"] = self.request_method
        return data