"""Auto-generated from TypeScript type: FinishPasskeyAuthenticationError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class FinishPasskeyAuthenticationErrorOriginNotAllowedDetails:
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["message"] = self.message
        return data



@dataclass
class FinishPasskeyAuthenticationErrorCannotParseAdditionalAllowedOrigin:
    type: Literal["CannotParseAdditionalAllowedOrigin"] = "CannotParseAdditionalAllowedOrigin"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyAuthenticationErrorNoAuthenticationChallengeFound:
    type: Literal["NoAuthenticationChallengeFound"] = "NoAuthenticationChallengeFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyAuthenticationErrorOriginNotAllowed:
    details: FinishPasskeyAuthenticationErrorOriginNotAllowedDetails
    type: Literal["OriginNotAllowed"] = "OriginNotAllowed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyAuthenticationErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




FinishPasskeyAuthenticationError = Union[
    FinishPasskeyAuthenticationErrorCannotParseAdditionalAllowedOrigin,
    FinishPasskeyAuthenticationErrorNoAuthenticationChallengeFound,
    FinishPasskeyAuthenticationErrorOriginNotAllowed,
    FinishPasskeyAuthenticationErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'FinishPasskeyAuthenticationError',
    'FinishPasskeyAuthenticationErrorCannotParseAdditionalAllowedOrigin',
    'FinishPasskeyAuthenticationErrorNoAuthenticationChallengeFound',
    'FinishPasskeyAuthenticationErrorOriginNotAllowed',
    'FinishPasskeyAuthenticationErrorUnexpectedError',
    'FinishPasskeyAuthenticationErrorOriginNotAllowedDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
