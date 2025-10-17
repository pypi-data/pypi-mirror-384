"""Auto-generated from TypeScript type: FetchAllActiveImpersonationSessionsResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .impersonation_session_info import ImpersonationSessionInfo


@dataclass
class FetchAllActiveImpersonationSessionsResponse:
    sessions: List[ImpersonationSessionInfo]
    has_more_results: bool
    next_paging_token: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessions"] = [item._to_request() for item in self.sessions]
        data["hasMoreResults"] = self.has_more_results
        if self.next_paging_token is not None:
            data["nextPagingToken"] = self.next_paging_token
        return data