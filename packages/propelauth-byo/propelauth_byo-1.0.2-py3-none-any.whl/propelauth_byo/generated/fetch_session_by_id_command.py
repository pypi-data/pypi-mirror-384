"""Auto-generated from TypeScript type: FetchSessionByIdCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FetchSessionByIdCommand:
    session_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        return data