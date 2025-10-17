"""Auto-generated from TypeScript type: InvalidateSessionByTokenError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class InvalidateSessionByTokenError:
    type: Literal["UnexpectedError"]
    details: UnexpectedErrorDetails

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        data["details"] = self.details
        return data