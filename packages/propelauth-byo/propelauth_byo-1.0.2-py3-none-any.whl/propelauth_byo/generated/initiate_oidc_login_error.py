"""Auto-generated from TypeScript type: InitiateOidcLoginError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class InitiateOidcLoginErrorRedirectUrlInvalidDetails:
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["message"] = self.message
        return data



@dataclass
class InitiateOidcLoginErrorClientNotFound:
    type: Literal["ClientNotFound"] = "ClientNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class InitiateOidcLoginErrorRedirectUrlInvalid:
    details: InitiateOidcLoginErrorRedirectUrlInvalidDetails
    type: Literal["RedirectUrlInvalid"] = "RedirectUrlInvalid"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class InitiateOidcLoginErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




InitiateOidcLoginError = Union[
    InitiateOidcLoginErrorClientNotFound,
    InitiateOidcLoginErrorRedirectUrlInvalid,
    InitiateOidcLoginErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'InitiateOidcLoginError',
    'InitiateOidcLoginErrorClientNotFound',
    'InitiateOidcLoginErrorRedirectUrlInvalid',
    'InitiateOidcLoginErrorUnexpectedError',
    'InitiateOidcLoginErrorRedirectUrlInvalidDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
