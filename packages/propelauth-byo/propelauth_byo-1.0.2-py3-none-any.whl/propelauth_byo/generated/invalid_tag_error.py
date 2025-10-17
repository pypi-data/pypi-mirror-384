"""Auto-generated from TypeScript type: InvalidTagError"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InvalidTagError:
    invalid_tag_format: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["InvalidTagFormat"] = self.invalid_tag_format
        return data