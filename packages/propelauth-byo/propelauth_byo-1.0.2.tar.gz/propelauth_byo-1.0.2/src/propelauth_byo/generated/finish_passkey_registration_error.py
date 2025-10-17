"""Auto-generated from TypeScript type: FinishPasskeyRegistrationError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class FinishPasskeyRegistrationErrorOriginNotAllowedDetails:
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["message"] = self.message
        return data



@dataclass
class FinishPasskeyRegistrationErrorCannotParseAdditionalAllowedOrigin:
    type: Literal["CannotParseAdditionalAllowedOrigin"] = "CannotParseAdditionalAllowedOrigin"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyRegistrationErrorNoRegistrationChallengeFound:
    type: Literal["NoRegistrationChallengeFound"] = "NoRegistrationChallengeFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyRegistrationErrorOriginNotAllowed:
    details: FinishPasskeyRegistrationErrorOriginNotAllowedDetails
    type: Literal["OriginNotAllowed"] = "OriginNotAllowed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyRegistrationErrorPasskeyForUserAlreadyExists:
    type: Literal["PasskeyForUserAlreadyExists"] = "PasskeyForUserAlreadyExists"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class FinishPasskeyRegistrationErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




FinishPasskeyRegistrationError = Union[
    FinishPasskeyRegistrationErrorCannotParseAdditionalAllowedOrigin,
    FinishPasskeyRegistrationErrorNoRegistrationChallengeFound,
    FinishPasskeyRegistrationErrorOriginNotAllowed,
    FinishPasskeyRegistrationErrorPasskeyForUserAlreadyExists,
    FinishPasskeyRegistrationErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'FinishPasskeyRegistrationError',
    'FinishPasskeyRegistrationErrorCannotParseAdditionalAllowedOrigin',
    'FinishPasskeyRegistrationErrorNoRegistrationChallengeFound',
    'FinishPasskeyRegistrationErrorOriginNotAllowed',
    'FinishPasskeyRegistrationErrorPasskeyForUserAlreadyExists',
    'FinishPasskeyRegistrationErrorUnexpectedError',
    'FinishPasskeyRegistrationErrorOriginNotAllowedDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
