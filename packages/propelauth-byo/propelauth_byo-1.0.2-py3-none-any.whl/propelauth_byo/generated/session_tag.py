"""Auto-generated from TypeScript type: SessionTag"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SessionTag:
    tag_name: str
    tag_value: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["tagName"] = self.tag_name
        data["tagValue"] = self.tag_value
        return data