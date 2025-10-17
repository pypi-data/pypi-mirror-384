"""Auto-generated from TypeScript type: StartPasskeyRegistrationError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class StartPasskeyRegistrationErrorTooManyPasskeysDetails:
    max_passkeys: int
    current_count: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["max_passkeys"] = self.max_passkeys
        data["current_count"] = self.current_count
        return data



@dataclass
class StartPasskeyRegistrationErrorCannotParseAdditionalAllowedOrigin:
    type: Literal["CannotParseAdditionalAllowedOrigin"] = "CannotParseAdditionalAllowedOrigin"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class StartPasskeyRegistrationErrorTooManyPasskeys:
    details: StartPasskeyRegistrationErrorTooManyPasskeysDetails
    type: Literal["TooManyPasskeys"] = "TooManyPasskeys"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class StartPasskeyRegistrationErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




StartPasskeyRegistrationError = Union[
    StartPasskeyRegistrationErrorCannotParseAdditionalAllowedOrigin,
    StartPasskeyRegistrationErrorTooManyPasskeys,
    StartPasskeyRegistrationErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'StartPasskeyRegistrationError',
    'StartPasskeyRegistrationErrorCannotParseAdditionalAllowedOrigin',
    'StartPasskeyRegistrationErrorTooManyPasskeys',
    'StartPasskeyRegistrationErrorUnexpectedError',
    'StartPasskeyRegistrationErrorTooManyPasskeysDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
