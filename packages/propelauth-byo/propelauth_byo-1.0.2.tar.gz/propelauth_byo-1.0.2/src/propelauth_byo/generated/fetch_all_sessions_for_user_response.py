"""Auto-generated from TypeScript type: FetchAllSessionsForUserResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .session_info import SessionInfo


@dataclass
class FetchAllSessionsForUserResponse:
    sessions: List[SessionInfo]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessions"] = [item._to_request() for item in self.sessions]
        return data