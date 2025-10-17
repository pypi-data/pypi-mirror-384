"""Auto-generated from TypeScript type: DeleteScimConnectionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class DeleteScimConnectionCommandScimConnectionId:
    scim_connection_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["scimConnectionId"] = self.scim_connection_id
        return data



@dataclass
class DeleteScimConnectionCommandCustomerId:
    customer_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        return data




DeleteScimConnectionCommand = Union[
    DeleteScimConnectionCommandScimConnectionId,
    DeleteScimConnectionCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'DeleteScimConnectionCommand',
    'DeleteScimConnectionCommandScimConnectionId',
    'DeleteScimConnectionCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
