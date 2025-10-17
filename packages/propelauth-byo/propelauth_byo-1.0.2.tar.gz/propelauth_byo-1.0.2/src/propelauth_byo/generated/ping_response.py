"""Auto-generated from TypeScript type: PingResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PingResponse:
    timestamp: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["timestamp"] = self.timestamp
        return data