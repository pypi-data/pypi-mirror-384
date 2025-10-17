"""Auto-generated from TypeScript type: FetchAllSessionsForUserCommand"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class FetchAllSessionsForUserCommand:
    user_id: str
    session_tags: Optional[List[str]] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        if self.session_tags is not None:
            data["sessionTags"] = self.session_tags
        return data