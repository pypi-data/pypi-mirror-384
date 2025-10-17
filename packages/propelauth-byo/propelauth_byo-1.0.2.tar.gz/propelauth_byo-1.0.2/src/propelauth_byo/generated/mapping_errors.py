"""Auto-generated from TypeScript type: MappingErrors"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .property_parse_error import PropertyParseError


@dataclass
class MappingErrors:
    errors: List[PropertyParseError]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["errors"] = [item._to_request() for item in self.errors]
        return data