"""Auto-generated from TypeScript type: PatchScimConnectionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class PatchScimConnectionErrorDisplayNameInvalidDetails:
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["message"] = self.message
        return data



@dataclass
class PatchScimConnectionErrorScimConnectionNotFound:
    type: Literal["ScimConnectionNotFound"] = "ScimConnectionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class PatchScimConnectionErrorDisplayNameInvalid:
    details: PatchScimConnectionErrorDisplayNameInvalidDetails
    type: Literal["DisplayNameInvalid"] = "DisplayNameInvalid"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class PatchScimConnectionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




PatchScimConnectionError = Union[
    PatchScimConnectionErrorScimConnectionNotFound,
    PatchScimConnectionErrorDisplayNameInvalid,
    PatchScimConnectionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'PatchScimConnectionError',
    'PatchScimConnectionErrorScimConnectionNotFound',
    'PatchScimConnectionErrorDisplayNameInvalid',
    'PatchScimConnectionErrorUnexpectedError',
    'PatchScimConnectionErrorDisplayNameInvalidDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
