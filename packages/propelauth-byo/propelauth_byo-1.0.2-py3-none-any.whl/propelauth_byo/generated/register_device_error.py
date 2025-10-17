"""Auto-generated from TypeScript type: RegisterDeviceError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class RegisterDeviceErrorNewDeviceChallengeRequiredDetails:
    device_challenge: str
    expires_at: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["deviceChallenge"] = self.device_challenge
        data["expiresAt"] = self.expires_at
        return data



@dataclass
class RegisterDeviceErrorSessionNotFound:
    type: Literal["SessionNotFound"] = "SessionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class RegisterDeviceErrorNewDeviceChallengeRequired:
    details: RegisterDeviceErrorNewDeviceChallengeRequiredDetails
    type: Literal["NewDeviceChallengeRequired"] = "NewDeviceChallengeRequired"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class RegisterDeviceErrorInvalidDeviceRegistration:
    type: Literal["InvalidDeviceRegistration"] = "InvalidDeviceRegistration"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class RegisterDeviceErrorDeviceAlreadyRegistered:
    type: Literal["DeviceAlreadyRegistered"] = "DeviceAlreadyRegistered"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class RegisterDeviceErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




RegisterDeviceError = Union[
    RegisterDeviceErrorSessionNotFound,
    RegisterDeviceErrorNewDeviceChallengeRequired,
    RegisterDeviceErrorInvalidDeviceRegistration,
    RegisterDeviceErrorDeviceAlreadyRegistered,
    RegisterDeviceErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'RegisterDeviceError',
    'RegisterDeviceErrorSessionNotFound',
    'RegisterDeviceErrorNewDeviceChallengeRequired',
    'RegisterDeviceErrorInvalidDeviceRegistration',
    'RegisterDeviceErrorDeviceAlreadyRegistered',
    'RegisterDeviceErrorUnexpectedError',
    'RegisterDeviceErrorNewDeviceChallengeRequiredDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
