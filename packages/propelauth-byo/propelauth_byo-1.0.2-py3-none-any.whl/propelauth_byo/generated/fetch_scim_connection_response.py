"""Auto-generated from TypeScript type: FetchScimConnectionResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .scim_user_mapping_config import ScimUserMappingConfig


@dataclass
class FetchScimConnectionResponse:
    connection_id: str
    customer_id: str
    user_mapping: ScimUserMappingConfig
    display_name: Optional[str] = None
    scim_api_key_valid_until: Optional[int] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["customerId"] = self.customer_id
        data["userMapping"] = self.user_mapping._to_request()
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.scim_api_key_valid_until is not None:
            data["scimApiKeyValidUntil"] = self.scim_api_key_valid_until
        return data