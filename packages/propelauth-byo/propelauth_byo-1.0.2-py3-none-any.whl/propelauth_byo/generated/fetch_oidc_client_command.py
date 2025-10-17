"""Auto-generated from TypeScript type: FetchOidcClientCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class FetchOidcClientCommandOidcClientId:
    oidc_client_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["oidcClientId"] = self.oidc_client_id
        return data



@dataclass
class FetchOidcClientCommandCustomerId:
    customer_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        return data




FetchOidcClientCommand = Union[
    FetchOidcClientCommandOidcClientId,
    FetchOidcClientCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'FetchOidcClientCommand',
    'FetchOidcClientCommandOidcClientId',
    'FetchOidcClientCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
