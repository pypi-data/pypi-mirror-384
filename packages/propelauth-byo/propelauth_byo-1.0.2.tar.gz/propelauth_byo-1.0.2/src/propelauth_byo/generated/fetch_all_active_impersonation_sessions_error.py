"""Auto-generated from TypeScript type: FetchAllActiveImpersonationSessionsError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class FetchAllActiveImpersonationSessionsErrorInvalidPagingToken:
    type: Literal["InvalidPagingToken"] = "InvalidPagingToken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class FetchAllActiveImpersonationSessionsErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




FetchAllActiveImpersonationSessionsError = Union[
    FetchAllActiveImpersonationSessionsErrorInvalidPagingToken,
    FetchAllActiveImpersonationSessionsErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'FetchAllActiveImpersonationSessionsError',
    'FetchAllActiveImpersonationSessionsErrorInvalidPagingToken',
    'FetchAllActiveImpersonationSessionsErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
