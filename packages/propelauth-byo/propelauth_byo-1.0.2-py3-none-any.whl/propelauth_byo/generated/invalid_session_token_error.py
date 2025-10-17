"""Auto-generated from TypeScript type: InvalidSessionTokenError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class InvalidSessionTokenErrorMalformedSessionToken:
    pass

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        return data



@dataclass
class InvalidSessionTokenErrorWrongTokenType:
    wrong_token_type: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["WrongTokenType"] = self.wrong_token_type
        return data



@dataclass
class InvalidSessionTokenErrorSessionTokenNotFound:
    pass

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        return data



@dataclass
class InvalidSessionTokenErrorMissingRequiredTags:
    missing_required_tags: List[str]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["MissingRequiredTags"] = self.missing_required_tags
        return data




InvalidSessionTokenError = Union[
    InvalidSessionTokenErrorMalformedSessionToken,
    InvalidSessionTokenErrorWrongTokenType,
    InvalidSessionTokenErrorSessionTokenNotFound,
    InvalidSessionTokenErrorMissingRequiredTags
]

# Export all types for client imports
__all__ = [
    'InvalidSessionTokenError',
    'InvalidSessionTokenErrorMalformedSessionToken',
    'InvalidSessionTokenErrorWrongTokenType',
    'InvalidSessionTokenErrorSessionTokenNotFound',
    'InvalidSessionTokenErrorMissingRequiredTags',
]

# Re-export UnexpectedErrorDetails if it was imported
