"""Auto-generated from TypeScript type: InvalidateImpersonationSessionByIdCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InvalidateImpersonationSessionByIdCommand:
    impersonation_session_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["impersonationSessionId"] = self.impersonation_session_id
        return data