"""Auto-generated from TypeScript type: ValidateSessionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_session_token_error import InvalidSessionTokenError
from .ip_matching_error import IpMatchingError
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class ValidateSessionErrorNewDeviceChallengeRequiredDetails:
    device_challenge: str
    expires_at: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["deviceChallenge"] = self.device_challenge
        data["expiresAt"] = self.expires_at
        return data



@dataclass
class ValidateSessionErrorInvalidSessionToken:
    details: InvalidSessionTokenError
    type: Literal["InvalidSessionToken"] = "InvalidSessionToken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ValidateSessionErrorIpAddressError:
    details: IpMatchingError
    type: Literal["IpAddressError"] = "IpAddressError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ValidateSessionErrorNewDeviceChallengeRequired:
    details: ValidateSessionErrorNewDeviceChallengeRequiredDetails
    type: Literal["NewDeviceChallengeRequired"] = "NewDeviceChallengeRequired"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ValidateSessionErrorDeviceVerificationRequired:
    type: Literal["DeviceVerificationRequired"] = "DeviceVerificationRequired"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ValidateSessionErrorDeviceVerificationFailed:
    type: Literal["DeviceVerificationFailed"] = "DeviceVerificationFailed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ValidateSessionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




ValidateSessionError = Union[
    ValidateSessionErrorInvalidSessionToken,
    ValidateSessionErrorIpAddressError,
    ValidateSessionErrorNewDeviceChallengeRequired,
    ValidateSessionErrorDeviceVerificationRequired,
    ValidateSessionErrorDeviceVerificationFailed,
    ValidateSessionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'ValidateSessionError',
    'ValidateSessionErrorInvalidSessionToken',
    'ValidateSessionErrorIpAddressError',
    'ValidateSessionErrorNewDeviceChallengeRequired',
    'ValidateSessionErrorDeviceVerificationRequired',
    'ValidateSessionErrorDeviceVerificationFailed',
    'ValidateSessionErrorUnexpectedError',
    'ValidateSessionErrorNewDeviceChallengeRequiredDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
