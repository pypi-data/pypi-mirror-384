"""Auto-generated from TypeScript type: InvalidateImpersonationSessionByTokenCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InvalidateImpersonationSessionByTokenCommand:
    impersonation_session_token: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["impersonationSessionToken"] = self.impersonation_session_token
        return data