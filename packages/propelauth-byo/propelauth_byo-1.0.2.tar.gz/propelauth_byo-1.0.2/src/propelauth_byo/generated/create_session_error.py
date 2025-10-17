"""Auto-generated from TypeScript type: CreateSessionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .ip_matching_error import IpMatchingError
from .invalid_tag_error import InvalidTagError
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class CreateSessionErrorSessionLimitExceededDetails:
    current_count: int
    max_allowed: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["currentCount"] = self.current_count
        data["maxAllowed"] = self.max_allowed
        return data



@dataclass
class CreateSessionErrorSessionLimitExceeded:
    details: CreateSessionErrorSessionLimitExceededDetails
    type: Literal["SessionLimitExceeded"] = "SessionLimitExceeded"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class CreateSessionErrorIpAddressError:
    details: IpMatchingError
    type: Literal["IpAddressError"] = "IpAddressError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class CreateSessionErrorTagParseError:
    details: InvalidTagError
    type: Literal["TagParseError"] = "TagParseError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class CreateSessionErrorInvalidDeviceRegistration:
    type: Literal["InvalidDeviceRegistration"] = "InvalidDeviceRegistration"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CreateSessionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CreateSessionError = Union[
    CreateSessionErrorSessionLimitExceeded,
    CreateSessionErrorIpAddressError,
    CreateSessionErrorTagParseError,
    CreateSessionErrorInvalidDeviceRegistration,
    CreateSessionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CreateSessionError',
    'CreateSessionErrorSessionLimitExceeded',
    'CreateSessionErrorIpAddressError',
    'CreateSessionErrorTagParseError',
    'CreateSessionErrorInvalidDeviceRegistration',
    'CreateSessionErrorUnexpectedError',
    'CreateSessionErrorSessionLimitExceededDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
