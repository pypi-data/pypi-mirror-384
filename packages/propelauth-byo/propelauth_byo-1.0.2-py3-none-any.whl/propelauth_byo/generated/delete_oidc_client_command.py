"""Auto-generated from TypeScript type: DeleteOidcClientCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class DeleteOidcClientCommandOidcClientId:
    oidc_client_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["oidcClientId"] = self.oidc_client_id
        return data



@dataclass
class DeleteOidcClientCommandCustomerId:
    customer_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        return data




DeleteOidcClientCommand = Union[
    DeleteOidcClientCommandOidcClientId,
    DeleteOidcClientCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'DeleteOidcClientCommand',
    'DeleteOidcClientCommandOidcClientId',
    'DeleteOidcClientCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
