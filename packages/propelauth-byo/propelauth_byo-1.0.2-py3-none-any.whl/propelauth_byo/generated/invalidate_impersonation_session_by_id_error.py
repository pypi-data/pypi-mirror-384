"""Auto-generated from TypeScript type: InvalidateImpersonationSessionByIdError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class InvalidateImpersonationSessionByIdErrorSessionNotFound:
    type: Literal["SessionNotFound"] = "SessionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class InvalidateImpersonationSessionByIdErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




InvalidateImpersonationSessionByIdError = Union[
    InvalidateImpersonationSessionByIdErrorSessionNotFound,
    InvalidateImpersonationSessionByIdErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'InvalidateImpersonationSessionByIdError',
    'InvalidateImpersonationSessionByIdErrorSessionNotFound',
    'InvalidateImpersonationSessionByIdErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
