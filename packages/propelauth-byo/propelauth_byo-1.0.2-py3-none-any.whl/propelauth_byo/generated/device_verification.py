"""Auto-generated from TypeScript type: DeviceVerification"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class DeviceVerification:
    signed_device_challenge: str
    request_url: Optional[str] = None
    request_method: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["signedDeviceChallenge"] = self.signed_device_challenge
        if self.request_url is not None:
            data["requestUrl"] = self.request_url
        if self.request_method is not None:
            data["requestMethod"] = self.request_method
        return data