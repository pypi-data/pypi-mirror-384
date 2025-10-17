"""Auto-generated from TypeScript type: ScimGroupMembershipResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ScimGroupMembershipResponse:
    group_id: str
    display_name: str
    external_id: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["groupId"] = self.group_id
        data["displayName"] = self.display_name
        if self.external_id is not None:
            data["externalId"] = self.external_id
        return data