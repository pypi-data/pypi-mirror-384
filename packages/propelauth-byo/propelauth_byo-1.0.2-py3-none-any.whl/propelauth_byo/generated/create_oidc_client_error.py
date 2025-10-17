"""Auto-generated from TypeScript type: CreateOidcClientError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_field import InvalidField
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class CreateOidcClientErrorInvalidFieldsDetails:
    fields: List[InvalidField]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["fields"] = [item._to_request() for item in self.fields]
        return data



@dataclass
class CreateOidcClientErrorInvalidFields:
    details: CreateOidcClientErrorInvalidFieldsDetails
    type: Literal["InvalidFields"] = "InvalidFields"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class CreateOidcClientErrorClientIdAlreadyTaken:
    type: Literal["ClientIdAlreadyTaken"] = "ClientIdAlreadyTaken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CreateOidcClientErrorCustomerIdAlreadyTakenForEoidcClient:
    type: Literal["CustomerIdAlreadyTakenForEoidcClient"] = "CustomerIdAlreadyTakenForEoidcClient"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class CreateOidcClientErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CreateOidcClientError = Union[
    CreateOidcClientErrorInvalidFields,
    CreateOidcClientErrorClientIdAlreadyTaken,
    CreateOidcClientErrorCustomerIdAlreadyTakenForEoidcClient,
    CreateOidcClientErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CreateOidcClientError',
    'CreateOidcClientErrorInvalidFields',
    'CreateOidcClientErrorClientIdAlreadyTaken',
    'CreateOidcClientErrorCustomerIdAlreadyTakenForEoidcClient',
    'CreateOidcClientErrorUnexpectedError',
    'CreateOidcClientErrorInvalidFieldsDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
