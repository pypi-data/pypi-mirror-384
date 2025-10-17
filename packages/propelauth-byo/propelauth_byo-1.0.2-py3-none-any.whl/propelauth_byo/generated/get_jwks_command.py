"""Auto-generated from TypeScript type: GetJwksCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class GetJwksCommand:
    pass

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        return data