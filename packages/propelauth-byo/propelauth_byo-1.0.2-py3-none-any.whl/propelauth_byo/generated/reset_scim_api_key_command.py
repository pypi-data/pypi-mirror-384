"""Auto-generated from TypeScript type: ResetScimApiKeyCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class ResetScimApiKeyCommandScimConnectionId:
    scim_connection_id: str
    scim_api_key_expiration: Optional[int]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["scimConnectionId"] = self.scim_connection_id
        if self.scim_api_key_expiration is not None:
            data["scimApiKeyExpiration"] = self.scim_api_key_expiration
        return data



@dataclass
class ResetScimApiKeyCommandCustomerId:
    customer_id: str
    scim_api_key_expiration: Optional[int]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        if self.scim_api_key_expiration is not None:
            data["scimApiKeyExpiration"] = self.scim_api_key_expiration
        return data




ResetScimApiKeyCommand = Union[
    ResetScimApiKeyCommandScimConnectionId,
    ResetScimApiKeyCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'ResetScimApiKeyCommand',
    'ResetScimApiKeyCommandScimConnectionId',
    'ResetScimApiKeyCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
