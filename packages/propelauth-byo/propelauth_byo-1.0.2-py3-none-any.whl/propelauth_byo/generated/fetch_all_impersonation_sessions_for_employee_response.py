"""Auto-generated from TypeScript type: FetchAllImpersonationSessionsForEmployeeResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .impersonation_session_info import ImpersonationSessionInfo


@dataclass
class FetchAllImpersonationSessionsForEmployeeResponse:
    sessions: List[ImpersonationSessionInfo]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessions"] = [item._to_request() for item in self.sessions]
        return data