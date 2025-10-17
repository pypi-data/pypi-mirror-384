"""Auto-generated from TypeScript type: CompleteScimUserResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .serde_json.json_value import JsonValue


@dataclass
class CompleteScimUserResponse:
    connection_id: str
    scim_user: JsonValue
    parsed_user_data: JsonValue
    active: bool
    primary_email: Optional[str] = None
    user_id: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["scimUser"] = self.scim_user
        data["parsedUserData"] = self.parsed_user_data
        data["active"] = self.active
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        if self.user_id is not None:
            data["userId"] = self.user_id
        return data