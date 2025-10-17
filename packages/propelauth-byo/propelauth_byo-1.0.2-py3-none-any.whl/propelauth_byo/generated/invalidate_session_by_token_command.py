"""Auto-generated from TypeScript type: InvalidateSessionByTokenCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class InvalidateSessionByTokenCommand:
    session_token: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.session_token is not None:
            data["sessionToken"] = self.session_token
        return data