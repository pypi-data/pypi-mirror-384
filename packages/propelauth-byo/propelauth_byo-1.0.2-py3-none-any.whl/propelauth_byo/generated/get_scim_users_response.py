"""Auto-generated from TypeScript type: GetScimUsersResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .complete_scim_user_response import CompleteScimUserResponse


@dataclass
class GetScimUsersResponse:
    connection_id: str
    users: List[CompleteScimUserResponse]
    page_number: int
    page_size: int
    total_results: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["users"] = [item._to_request() for item in self.users]
        data["pageNumber"] = self.page_number
        data["pageSize"] = self.page_size
        data["totalResults"] = self.total_results
        return data