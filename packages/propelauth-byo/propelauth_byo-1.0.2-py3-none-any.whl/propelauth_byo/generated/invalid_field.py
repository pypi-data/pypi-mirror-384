"""Auto-generated from TypeScript type: InvalidField"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InvalidField:
    field: str
    code: str
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        data["code"] = self.code
        data["message"] = self.message
        return data