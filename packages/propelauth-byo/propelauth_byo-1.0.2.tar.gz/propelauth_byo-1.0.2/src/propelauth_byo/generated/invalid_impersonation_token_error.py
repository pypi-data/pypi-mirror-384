"""Auto-generated from TypeScript type: InvalidImpersonationTokenError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class InvalidImpersonationTokenErrorMalformedToken:
    pass

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        return data



@dataclass
class InvalidImpersonationTokenErrorWrongTokenType:
    wrong_token_type: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["WrongTokenType"] = self.wrong_token_type
        return data




InvalidImpersonationTokenError = Union[
    InvalidImpersonationTokenErrorMalformedToken,
    InvalidImpersonationTokenErrorWrongTokenType
]

# Export all types for client imports
__all__ = [
    'InvalidImpersonationTokenError',
    'InvalidImpersonationTokenErrorMalformedToken',
    'InvalidImpersonationTokenErrorWrongTokenType',
]

# Re-export UnexpectedErrorDetails if it was imported
