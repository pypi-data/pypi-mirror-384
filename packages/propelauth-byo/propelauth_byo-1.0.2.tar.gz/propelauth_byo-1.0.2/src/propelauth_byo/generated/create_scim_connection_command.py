"""Auto-generated from TypeScript type: CreateScimConnectionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .scim_user_mapping_config import ScimUserMappingConfig


@dataclass
class CreateScimConnectionCommand:
    customer_id: str
    display_name: Optional[str] = None
    scim_api_key_expiration: Optional[int] = None
    custom_mapping: Optional[ScimUserMappingConfig] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.scim_api_key_expiration is not None:
            data["scimApiKeyExpiration"] = self.scim_api_key_expiration
        if self.custom_mapping is not None:
            data["customMapping"] = self.custom_mapping._to_request()
        return data