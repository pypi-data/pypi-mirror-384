"""Auto-generated from TypeScript type: GetScimUserResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .complete_scim_user_response import CompleteScimUserResponse
from .scim_group_membership_response import ScimGroupMembershipResponse


@dataclass
class GetScimUserResponse:
    connection_id: str
    user: CompleteScimUserResponse
    groups: List[ScimGroupMembershipResponse]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["user"] = self.user._to_request()
        data["groups"] = [item._to_request() for item in self.groups]
        return data