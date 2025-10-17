"""Auto-generated from TypeScript type: FetchAllSessionsResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .session_info import SessionInfo


@dataclass
class FetchAllSessionsResponse:
    items: List[SessionInfo]
    page: int
    page_size: int
    total_count: int
    has_more_results: bool

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["items"] = [item._to_request() for item in self.items]
        data["page"] = self.page
        data["pageSize"] = self.page_size
        data["totalCount"] = self.total_count
        data["hasMoreResults"] = self.has_more_results
        return data