"""Auto-generated from TypeScript type: DeregisterPasskeyError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class DeregisterPasskeyErrorPasskeyNotFound:
    type: Literal["PasskeyNotFound"] = "PasskeyNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class DeregisterPasskeyErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




DeregisterPasskeyError = Union[
    DeregisterPasskeyErrorPasskeyNotFound,
    DeregisterPasskeyErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'DeregisterPasskeyError',
    'DeregisterPasskeyErrorPasskeyNotFound',
    'DeregisterPasskeyErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
