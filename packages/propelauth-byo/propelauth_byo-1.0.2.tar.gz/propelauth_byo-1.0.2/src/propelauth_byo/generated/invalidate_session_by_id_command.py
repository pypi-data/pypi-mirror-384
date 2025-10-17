"""Auto-generated from TypeScript type: InvalidateSessionByIdCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class InvalidateSessionByIdCommand:
    session_id: str
    user_id: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        if self.user_id is not None:
            data["userId"] = self.user_id
        return data