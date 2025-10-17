"""Auto-generated from TypeScript type: InvalidateImpersonationSessionByTokenError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class InvalidateImpersonationSessionByTokenErrorSessionNotFound:
    type: Literal["SessionNotFound"] = "SessionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class InvalidateImpersonationSessionByTokenErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




InvalidateImpersonationSessionByTokenError = Union[
    InvalidateImpersonationSessionByTokenErrorSessionNotFound,
    InvalidateImpersonationSessionByTokenErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'InvalidateImpersonationSessionByTokenError',
    'InvalidateImpersonationSessionByTokenErrorSessionNotFound',
    'InvalidateImpersonationSessionByTokenErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
