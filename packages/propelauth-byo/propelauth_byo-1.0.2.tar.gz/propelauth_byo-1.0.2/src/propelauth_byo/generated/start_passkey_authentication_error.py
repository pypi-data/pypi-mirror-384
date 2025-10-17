"""Auto-generated from TypeScript type: StartPasskeyAuthenticationError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class StartPasskeyAuthenticationErrorCannotParseAdditionalAllowedOrigin:
    type: Literal["CannotParseAdditionalAllowedOrigin"] = "CannotParseAdditionalAllowedOrigin"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class StartPasskeyAuthenticationErrorNoPasskeysRegisteredForUser:
    type: Literal["NoPasskeysRegisteredForUser"] = "NoPasskeysRegisteredForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class StartPasskeyAuthenticationErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




StartPasskeyAuthenticationError = Union[
    StartPasskeyAuthenticationErrorCannotParseAdditionalAllowedOrigin,
    StartPasskeyAuthenticationErrorNoPasskeysRegisteredForUser,
    StartPasskeyAuthenticationErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'StartPasskeyAuthenticationError',
    'StartPasskeyAuthenticationErrorCannotParseAdditionalAllowedOrigin',
    'StartPasskeyAuthenticationErrorNoPasskeysRegisteredForUser',
    'StartPasskeyAuthenticationErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
