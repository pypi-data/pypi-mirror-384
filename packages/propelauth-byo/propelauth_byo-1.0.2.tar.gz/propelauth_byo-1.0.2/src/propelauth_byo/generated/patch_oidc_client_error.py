"""Auto-generated from TypeScript type: PatchOidcClientError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_field import InvalidField
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class PatchOidcClientErrorInvalidFieldsDetails:
    fields: List[InvalidField]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["fields"] = [item._to_request() for item in self.fields]
        return data



@dataclass
class PatchOidcClientErrorOidcClientNotFound:
    type: Literal["OidcClientNotFound"] = "OidcClientNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class PatchOidcClientErrorInvalidFields:
    details: PatchOidcClientErrorInvalidFieldsDetails
    type: Literal["InvalidFields"] = "InvalidFields"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class PatchOidcClientErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




PatchOidcClientError = Union[
    PatchOidcClientErrorOidcClientNotFound,
    PatchOidcClientErrorInvalidFields,
    PatchOidcClientErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'PatchOidcClientError',
    'PatchOidcClientErrorOidcClientNotFound',
    'PatchOidcClientErrorInvalidFields',
    'PatchOidcClientErrorUnexpectedError',
    'PatchOidcClientErrorInvalidFieldsDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
