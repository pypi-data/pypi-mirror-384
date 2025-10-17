"""Auto-generated from TypeScript type: CommitScimUserChangeCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CommitScimUserChangeCommand:
    connection_id: str
    commit_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["commitId"] = self.commit_id
        return data