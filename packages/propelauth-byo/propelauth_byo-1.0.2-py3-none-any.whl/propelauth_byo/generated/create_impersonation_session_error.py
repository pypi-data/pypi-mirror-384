"""Auto-generated from TypeScript type: CreateImpersonationSessionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class CreateImpersonationSessionErrorImpersonationDisabled:
    type: Literal["ImpersonationDisabled"] = "ImpersonationDisabled"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CreateImpersonationSessionErrorUnauthorizedEmployee:
    details: str
    type: Literal["UnauthorizedEmployee"] = "UnauthorizedEmployee"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class CreateImpersonationSessionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CreateImpersonationSessionError = Union[
    CreateImpersonationSessionErrorImpersonationDisabled,
    CreateImpersonationSessionErrorUnauthorizedEmployee,
    CreateImpersonationSessionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CreateImpersonationSessionError',
    'CreateImpersonationSessionErrorImpersonationDisabled',
    'CreateImpersonationSessionErrorUnauthorizedEmployee',
    'CreateImpersonationSessionErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
