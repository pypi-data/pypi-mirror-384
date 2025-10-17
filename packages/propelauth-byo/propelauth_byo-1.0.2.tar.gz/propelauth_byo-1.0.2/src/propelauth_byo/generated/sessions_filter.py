"""Auto-generated from TypeScript type: SessionsFilter"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class SessionsFilter:
    user_id: Optional[str] = None
    session_tags: Optional[List[str]] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.user_id is not None:
            data["userId"] = self.user_id
        if self.session_tags is not None:
            data["sessionTags"] = self.session_tags
        return data