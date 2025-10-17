"""Auto-generated from TypeScript type: FetchAllActiveImpersonationSessionsCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class FetchAllActiveImpersonationSessionsCommand:
    paging_token: Optional[str] = None
    employee_email: Optional[str] = None
    target_user_id: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.paging_token is not None:
            data["pagingToken"] = self.paging_token
        if self.employee_email is not None:
            data["employeeEmail"] = self.employee_email
        if self.target_user_id is not None:
            data["targetUserId"] = self.target_user_id
        return data