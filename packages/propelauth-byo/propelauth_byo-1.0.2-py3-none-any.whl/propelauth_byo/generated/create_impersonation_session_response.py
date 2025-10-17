"""Auto-generated from TypeScript type: CreateImpersonationSessionResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CreateImpersonationSessionResponse:
    session_id: str
    impersonation_session_token: str
    expires_at: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        data["impersonationSessionToken"] = self.impersonation_session_token
        data["expiresAt"] = self.expires_at
        return data