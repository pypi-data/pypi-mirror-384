"""Auto-generated from TypeScript type: GetScimUsersError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class GetScimUsersErrorInvalidQueryFieldDetails:
    field: str
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        data["message"] = self.message
        return data



@dataclass
class GetScimUsersErrorScimConnectionNotFound:
    type: Literal["ScimConnectionNotFound"] = "ScimConnectionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class GetScimUsersErrorInvalidQueryField:
    details: GetScimUsersErrorInvalidQueryFieldDetails
    type: Literal["InvalidQueryField"] = "InvalidQueryField"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class GetScimUsersErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




GetScimUsersError = Union[
    GetScimUsersErrorScimConnectionNotFound,
    GetScimUsersErrorInvalidQueryField,
    GetScimUsersErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'GetScimUsersError',
    'GetScimUsersErrorScimConnectionNotFound',
    'GetScimUsersErrorInvalidQueryField',
    'GetScimUsersErrorUnexpectedError',
    'GetScimUsersErrorInvalidQueryFieldDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
