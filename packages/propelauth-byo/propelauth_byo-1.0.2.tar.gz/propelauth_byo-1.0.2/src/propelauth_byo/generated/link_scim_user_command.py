"""Auto-generated from TypeScript type: LinkScimUserCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class LinkScimUserCommand:
    connection_id: str
    commit_id: str
    user_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        return data