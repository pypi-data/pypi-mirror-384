"""Auto-generated from TypeScript type: InvalidateAllImpersonationSessionsForUserCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InvalidateAllImpersonationSessionsForUserCommand:
    user_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        return data