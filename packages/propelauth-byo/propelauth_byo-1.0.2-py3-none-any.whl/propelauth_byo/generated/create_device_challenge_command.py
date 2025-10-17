"""Auto-generated from TypeScript type: CreateDeviceChallengeCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class CreateDeviceChallengeCommand:
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.user_agent is not None:
            data["userAgent"] = self.user_agent
        if self.ip_address is not None:
            data["ipAddress"] = self.ip_address
        return data