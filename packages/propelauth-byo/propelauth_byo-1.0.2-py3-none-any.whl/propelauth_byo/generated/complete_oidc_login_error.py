"""Auto-generated from TypeScript type: CompleteOidcLoginError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .oidc_login_request_error import OidcLoginRequestError
from .identity_provider_error import IdentityProviderError
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class CompleteOidcLoginErrorLoginBlockedByEmailAllowlist:
    type: Literal["LoginBlockedByEmailAllowlist"] = "LoginBlockedByEmailAllowlist"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CompleteOidcLoginErrorScimUserNotFoundWhereExpected:
    type: Literal["ScimUserNotFoundWhereExpected"] = "ScimUserNotFoundWhereExpected"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CompleteOidcLoginErrorScimUserNotActive:
    type: Literal["ScimUserNotActive"] = "ScimUserNotActive"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CompleteOidcLoginErrorInvalidLoginRequest:
    details: OidcLoginRequestError
    type: Literal["InvalidLoginRequest"] = "InvalidLoginRequest"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class CompleteOidcLoginErrorIdentityProviderError:
    details: IdentityProviderError
    type: Literal["IdentityProviderError"] = "IdentityProviderError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class CompleteOidcLoginErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CompleteOidcLoginError = Union[
    CompleteOidcLoginErrorLoginBlockedByEmailAllowlist,
    CompleteOidcLoginErrorScimUserNotFoundWhereExpected,
    CompleteOidcLoginErrorScimUserNotActive,
    CompleteOidcLoginErrorInvalidLoginRequest,
    CompleteOidcLoginErrorIdentityProviderError,
    CompleteOidcLoginErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CompleteOidcLoginError',
    'CompleteOidcLoginErrorLoginBlockedByEmailAllowlist',
    'CompleteOidcLoginErrorScimUserNotFoundWhereExpected',
    'CompleteOidcLoginErrorScimUserNotActive',
    'CompleteOidcLoginErrorInvalidLoginRequest',
    'CompleteOidcLoginErrorIdentityProviderError',
    'CompleteOidcLoginErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
