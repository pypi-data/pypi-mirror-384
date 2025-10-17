"""Auto-generated from TypeScript type: FetchAllSessionsCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class FetchAllSessionsCommand:
    user_id: Optional[str] = None
    session_tags: Optional[List[str]] = None
    page: Optional[int] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.user_id is not None:
            data["userId"] = self.user_id
        if self.session_tags is not None:
            data["sessionTags"] = self.session_tags
        if self.page is not None:
            data["page"] = self.page
        return data