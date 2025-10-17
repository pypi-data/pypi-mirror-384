"""Auto-generated from TypeScript type: GetScimUserCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class GetScimUserCommandScimConnectionId:
    user_id: str
    scim_connection_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        data["scimConnectionId"] = self.scim_connection_id
        return data



@dataclass
class GetScimUserCommandCustomerId:
    user_id: str
    customer_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        data["customerId"] = self.customer_id
        return data




GetScimUserCommand = Union[
    GetScimUserCommandScimConnectionId,
    GetScimUserCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'GetScimUserCommand',
    'GetScimUserCommandScimConnectionId',
    'GetScimUserCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
