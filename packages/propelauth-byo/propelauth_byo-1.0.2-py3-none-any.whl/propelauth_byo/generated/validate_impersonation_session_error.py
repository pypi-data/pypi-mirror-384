"""Auto-generated from TypeScript type: ValidateImpersonationSessionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_impersonation_token_error import InvalidImpersonationTokenError
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class ValidateImpersonationSessionErrorImpersonationNotEnabled:
    type: Literal["ImpersonationNotEnabled"] = "ImpersonationNotEnabled"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ValidateImpersonationSessionErrorInvalidImpersonationToken:
    details: InvalidImpersonationTokenError
    type: Literal["InvalidImpersonationToken"] = "InvalidImpersonationToken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ValidateImpersonationSessionErrorSessionNotFound:
    type: Literal["SessionNotFound"] = "SessionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ValidateImpersonationSessionErrorIpAddressMismatch:
    type: Literal["IpAddressMismatch"] = "IpAddressMismatch"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ValidateImpersonationSessionErrorUserAgentMismatch:
    type: Literal["UserAgentMismatch"] = "UserAgentMismatch"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ValidateImpersonationSessionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




ValidateImpersonationSessionError = Union[
    ValidateImpersonationSessionErrorImpersonationNotEnabled,
    ValidateImpersonationSessionErrorInvalidImpersonationToken,
    ValidateImpersonationSessionErrorSessionNotFound,
    ValidateImpersonationSessionErrorIpAddressMismatch,
    ValidateImpersonationSessionErrorUserAgentMismatch,
    ValidateImpersonationSessionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'ValidateImpersonationSessionError',
    'ValidateImpersonationSessionErrorImpersonationNotEnabled',
    'ValidateImpersonationSessionErrorInvalidImpersonationToken',
    'ValidateImpersonationSessionErrorSessionNotFound',
    'ValidateImpersonationSessionErrorIpAddressMismatch',
    'ValidateImpersonationSessionErrorUserAgentMismatch',
    'ValidateImpersonationSessionErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
