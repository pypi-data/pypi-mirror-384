"""Auto-generated from TypeScript type: LinkScimUserError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class LinkScimUserErrorScimConnectionNotFound:
    type: Literal["ScimConnectionNotFound"] = "ScimConnectionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class LinkScimUserErrorUserNotFound:
    type: Literal["UserNotFound"] = "UserNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class LinkScimUserErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




LinkScimUserError = Union[
    LinkScimUserErrorScimConnectionNotFound,
    LinkScimUserErrorUserNotFound,
    LinkScimUserErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'LinkScimUserError',
    'LinkScimUserErrorScimConnectionNotFound',
    'LinkScimUserErrorUserNotFound',
    'LinkScimUserErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
