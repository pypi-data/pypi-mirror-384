"""Auto-generated from TypeScript type: CreateImpersonationSessionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .serde_json.json_value import JsonValue


@dataclass
class CreateImpersonationSessionCommand:
    employee_email: str
    target_user_id: str
    user_agent: str
    ip_address: str
    metadata: Optional[JsonValue] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["employeeEmail"] = self.employee_email
        data["targetUserId"] = self.target_user_id
        data["userAgent"] = self.user_agent
        data["ipAddress"] = self.ip_address
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return data