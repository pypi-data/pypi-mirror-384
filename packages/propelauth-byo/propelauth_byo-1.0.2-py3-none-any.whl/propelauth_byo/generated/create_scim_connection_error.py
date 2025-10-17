"""Auto-generated from TypeScript type: CreateScimConnectionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_field import InvalidField
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class CreateScimConnectionErrorInvalidFieldsDetails:
    fields: List[InvalidField]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["fields"] = [item._to_request() for item in self.fields]
        return data



@dataclass
class CreateScimConnectionErrorInvalidFields:
    details: CreateScimConnectionErrorInvalidFieldsDetails
    type: Literal["InvalidFields"] = "InvalidFields"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class CreateScimConnectionErrorScimConnectionForCustomerIdAlreadyExists:
    type: Literal["ScimConnectionForCustomerIdAlreadyExists"] = "ScimConnectionForCustomerIdAlreadyExists"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CreateScimConnectionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CreateScimConnectionError = Union[
    CreateScimConnectionErrorInvalidFields,
    CreateScimConnectionErrorScimConnectionForCustomerIdAlreadyExists,
    CreateScimConnectionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CreateScimConnectionError',
    'CreateScimConnectionErrorInvalidFields',
    'CreateScimConnectionErrorScimConnectionForCustomerIdAlreadyExists',
    'CreateScimConnectionErrorUnexpectedError',
    'CreateScimConnectionErrorInvalidFieldsDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
