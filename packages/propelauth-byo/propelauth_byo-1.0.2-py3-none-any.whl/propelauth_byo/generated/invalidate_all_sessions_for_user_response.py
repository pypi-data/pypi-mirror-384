"""Auto-generated from TypeScript type: InvalidateAllSessionsForUserResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InvalidateAllSessionsForUserResponse:
    sessions_invalidated: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionsInvalidated"] = self.sessions_invalidated
        return data