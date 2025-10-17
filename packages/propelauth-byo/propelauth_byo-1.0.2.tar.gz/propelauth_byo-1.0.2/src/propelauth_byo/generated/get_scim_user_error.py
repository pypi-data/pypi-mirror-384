"""Auto-generated from TypeScript type: GetScimUserError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class GetScimUserErrorScimConnectionNotFound:
    type: Literal["ScimConnectionNotFound"] = "ScimConnectionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class GetScimUserErrorUserNotFound:
    type: Literal["UserNotFound"] = "UserNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class GetScimUserErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




GetScimUserError = Union[
    GetScimUserErrorScimConnectionNotFound,
    GetScimUserErrorUserNotFound,
    GetScimUserErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'GetScimUserError',
    'GetScimUserErrorScimConnectionNotFound',
    'GetScimUserErrorUserNotFound',
    'GetScimUserErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
