"""Auto-generated from TypeScript type: ValidateImpersonationSessionCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ValidateImpersonationSessionCommand:
    impersonation_token: str
    user_agent: str
    ip_address: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["impersonationToken"] = self.impersonation_token
        data["userAgent"] = self.user_agent
        data["ipAddress"] = self.ip_address
        return data