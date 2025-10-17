"""Auto-generated from TypeScript type: IntegrationKeyError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class IntegrationKeyErrorCommandNotAllowedDetails:
    command_name: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["command_name"] = self.command_name
        return data



@dataclass
class IntegrationKeyErrorInvalidPrefix:
    details: str
    type: Literal["InvalidPrefix"] = "InvalidPrefix"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class IntegrationKeyErrorIntegrationKeyNotFound:
    type: Literal["IntegrationKeyNotFound"] = "IntegrationKeyNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class IntegrationKeyErrorNoIntegrationKeyFoundInHeader:
    type: Literal["NoIntegrationKeyFoundInHeader"] = "NoIntegrationKeyFoundInHeader"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class IntegrationKeyErrorCommandNotAllowed:
    details: IntegrationKeyErrorCommandNotAllowedDetails
    type: Literal["CommandNotAllowed"] = "CommandNotAllowed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class IntegrationKeyErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




IntegrationKeyError = Union[
    IntegrationKeyErrorInvalidPrefix,
    IntegrationKeyErrorIntegrationKeyNotFound,
    IntegrationKeyErrorNoIntegrationKeyFoundInHeader,
    IntegrationKeyErrorCommandNotAllowed,
    IntegrationKeyErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'IntegrationKeyError',
    'IntegrationKeyErrorInvalidPrefix',
    'IntegrationKeyErrorIntegrationKeyNotFound',
    'IntegrationKeyErrorNoIntegrationKeyFoundInHeader',
    'IntegrationKeyErrorCommandNotAllowed',
    'IntegrationKeyErrorUnexpectedError',
    'IntegrationKeyErrorCommandNotAllowedDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
