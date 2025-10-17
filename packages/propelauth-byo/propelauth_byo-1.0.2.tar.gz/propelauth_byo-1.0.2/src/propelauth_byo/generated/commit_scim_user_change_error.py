"""Auto-generated from TypeScript type: CommitScimUserChangeError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class CommitScimUserChangeErrorScimConnectionNotFound:
    type: Literal["ScimConnectionNotFound"] = "ScimConnectionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CommitScimUserChangeErrorStagedChangeNotFound:
    type: Literal["StagedChangeNotFound"] = "StagedChangeNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CommitScimUserChangeErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CommitScimUserChangeError = Union[
    CommitScimUserChangeErrorScimConnectionNotFound,
    CommitScimUserChangeErrorStagedChangeNotFound,
    CommitScimUserChangeErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CommitScimUserChangeError',
    'CommitScimUserChangeErrorScimConnectionNotFound',
    'CommitScimUserChangeErrorStagedChangeNotFound',
    'CommitScimUserChangeErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
