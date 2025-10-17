"""Auto-generated from TypeScript type: FetchScimConnectionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class FetchScimConnectionCommandScimConnectionId:
    scim_connection_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["scimConnectionId"] = self.scim_connection_id
        return data



@dataclass
class FetchScimConnectionCommandCustomerId:
    customer_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        return data




FetchScimConnectionCommand = Union[
    FetchScimConnectionCommandScimConnectionId,
    FetchScimConnectionCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'FetchScimConnectionCommand',
    'FetchScimConnectionCommandScimConnectionId',
    'FetchScimConnectionCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
