"""Auto-generated from TypeScript type: ScimUserWithWarnings"""
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ScimUserWithWarnings:
    external_user_id: str
    user_name: str
    missing_fields: List[str]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["externalUserId"] = self.external_user_id
        data["userName"] = self.user_name
        data["missingFields"] = self.missing_fields
        return data