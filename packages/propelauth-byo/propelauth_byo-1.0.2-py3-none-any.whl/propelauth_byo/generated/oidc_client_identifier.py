"""Auto-generated from TypeScript type: OidcClientIdentifier"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class OidcClientIdentifierOidcClientId:
    oidc_client_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["oidcClientId"] = self.oidc_client_id
        return data



@dataclass
class OidcClientIdentifierCustomerId:
    customer_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        return data




OidcClientIdentifier = Union[
    OidcClientIdentifierOidcClientId,
    OidcClientIdentifierCustomerId
]

# Export all types for client imports
__all__ = [
    'OidcClientIdentifier',
    'OidcClientIdentifierOidcClientId',
    'OidcClientIdentifierCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
