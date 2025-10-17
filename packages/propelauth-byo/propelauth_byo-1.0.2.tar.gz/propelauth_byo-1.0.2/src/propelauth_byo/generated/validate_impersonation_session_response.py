"""Auto-generated from TypeScript type: ValidateImpersonationSessionResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Any, Optional


@dataclass
class ValidateImpersonationSessionResponse:
    impersonation_session_id: str
    employee_email: str
    target_user_id: str
    created_at: int
    expires_at: int
    metadata: Optional[Any] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["impersonationSessionId"] = self.impersonation_session_id
        data["employeeEmail"] = self.employee_email
        data["targetUserId"] = self.target_user_id
        data["createdAt"] = self.created_at
        data["expiresAt"] = self.expires_at
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return data