"""Auto-generated from TypeScript type: RegisterDeviceResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RegisterDeviceResponse:
    new_device_detected: bool

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["newDeviceDetected"] = self.new_device_detected
        return data