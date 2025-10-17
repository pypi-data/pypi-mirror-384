"""Auto-generated from TypeScript type: GetScimUsersCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .scim_users_page_equality_filter import ScimUsersPageEqualityFilter


@dataclass
class GetScimUsersCommandScimConnectionId:
    scim_connection_id: str
    filter: Optional[ScimUsersPageEqualityFilter]
    page_number: Optional[int]
    page_size: Optional[int]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["scimConnectionId"] = self.scim_connection_id
        if self.filter is not None:
            data["filter"] = self.filter._to_request()
        if self.page_number is not None:
            data["pageNumber"] = self.page_number
        if self.page_size is not None:
            data["pageSize"] = self.page_size
        return data



@dataclass
class GetScimUsersCommandCustomerId:
    customer_id: str
    filter: Optional[ScimUsersPageEqualityFilter]
    page_number: Optional[int]
    page_size: Optional[int]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        if self.filter is not None:
            data["filter"] = self.filter._to_request()
        if self.page_number is not None:
            data["pageNumber"] = self.page_number
        if self.page_size is not None:
            data["pageSize"] = self.page_size
        return data




GetScimUsersCommand = Union[
    GetScimUsersCommandScimConnectionId,
    GetScimUsersCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'GetScimUsersCommand',
    'GetScimUsersCommandScimConnectionId',
    'GetScimUsersCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
