"""Auto-generated from TypeScript type: ScimUsersWithWarningsPage"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .scim_user_with_warnings import ScimUserWithWarnings


@dataclass
class ScimUsersWithWarningsPage:
    users: List[ScimUserWithWarnings]
    total_count: int
    page: int
    page_size: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["users"] = [item._to_request() for item in self.users]
        data["totalCount"] = self.total_count
        data["page"] = self.page
        data["pageSize"] = self.page_size
        return data