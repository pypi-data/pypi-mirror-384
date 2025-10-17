"""Auto-generated from TypeScript type: UpdateSessionsResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class UpdateSessionsResponse:
    updated_count: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["updatedCount"] = self.updated_count
        return data