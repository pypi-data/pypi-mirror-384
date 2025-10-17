"""Auto-generated from TypeScript type: DeviceInfo"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .device_type import DeviceType


@dataclass
class DeviceInfo:
    display_name: str
    device_type: DeviceType
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["displayName"] = self.display_name
        data["deviceType"] = self.device_type
        if self.browser is not None:
            data["browser"] = self.browser
        if self.browser_version is not None:
            data["browserVersion"] = self.browser_version
        if self.os is not None:
            data["os"] = self.os
        if self.os_version is not None:
            data["osVersion"] = self.os_version
        return data