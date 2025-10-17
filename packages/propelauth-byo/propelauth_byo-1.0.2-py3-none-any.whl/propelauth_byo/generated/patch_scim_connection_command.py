"""Auto-generated from TypeScript type: PatchScimConnectionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .scim_user_mapping_config import ScimUserMappingConfig


@dataclass
class PatchScimConnectionCommandScimConnectionId:
    scim_connection_id: str
    display_name: Optional[str]
    scim_api_key_expiration: Optional[int]
    custom_mapping: Optional[ScimUserMappingConfig]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["scimConnectionId"] = self.scim_connection_id
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.scim_api_key_expiration is not None:
            data["scimApiKeyExpiration"] = self.scim_api_key_expiration
        if self.custom_mapping is not None:
            data["customMapping"] = self.custom_mapping._to_request()
        return data



@dataclass
class PatchScimConnectionCommandCustomerId:
    customer_id: str
    display_name: Optional[str]
    scim_api_key_expiration: Optional[int]
    custom_mapping: Optional[ScimUserMappingConfig]

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




PatchScimConnectionCommand = Union[
    PatchScimConnectionCommandScimConnectionId,
    PatchScimConnectionCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'PatchScimConnectionCommand',
    'PatchScimConnectionCommandScimConnectionId',
    'PatchScimConnectionCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
