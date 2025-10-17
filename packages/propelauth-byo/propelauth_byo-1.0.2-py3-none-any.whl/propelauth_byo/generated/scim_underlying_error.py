"""Auto-generated from TypeScript type: ScimUnderlyingError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class ScimUnderlyingErrorMissingRequiredFieldDetails:
    field: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        return data


@dataclass
class ScimUnderlyingErrorCantRemoveRequiredFieldDetails:
    field: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        return data


@dataclass
class ScimUnderlyingErrorScimUserIdAlreadyTakenDetails:
    field: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        return data


@dataclass
class ScimUnderlyingErrorInvalidQueryFieldDetails:
    field: str
    message: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        data["message"] = self.message
        return data


@dataclass
class ScimUnderlyingErrorInvalidPatchValueDetails:
    field: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["field"] = self.field
        return data



@dataclass
class ScimUnderlyingErrorInvalidApiKey:
    type: Literal["InvalidApiKey"] = "InvalidApiKey"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidPath:
    type: Literal["InvalidPath"] = "InvalidPath"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorUserNotFound:
    type: Literal["UserNotFound"] = "UserNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorGroupNotFound:
    type: Literal["GroupNotFound"] = "GroupNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorMissingRequiredField:
    details: ScimUnderlyingErrorMissingRequiredFieldDetails
    type: Literal["MissingRequiredField"] = "MissingRequiredField"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorCantRemoveRequiredField:
    details: ScimUnderlyingErrorCantRemoveRequiredFieldDetails
    type: Literal["CantRemoveRequiredField"] = "CantRemoveRequiredField"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorScimUserIdAlreadyTaken:
    details: ScimUnderlyingErrorScimUserIdAlreadyTakenDetails
    type: Literal["ScimUserIdAlreadyTaken"] = "ScimUserIdAlreadyTaken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidBody:
    type: Literal["InvalidBody"] = "InvalidBody"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidQueryField:
    details: ScimUnderlyingErrorInvalidQueryFieldDetails
    type: Literal["InvalidQueryField"] = "InvalidQueryField"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidPatchPath:
    type: Literal["InvalidPatchPath"] = "InvalidPatchPath"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidPatchOperation:
    type: Literal["InvalidPatchOperation"] = "InvalidPatchOperation"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidPatchValue:
    details: ScimUnderlyingErrorInvalidPatchValueDetails
    type: Literal["InvalidPatchValue"] = "InvalidPatchValue"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorInvalidSchema:
    type: Literal["InvalidSchema"] = "InvalidSchema"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class ScimUnderlyingErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




ScimUnderlyingError = Union[
    ScimUnderlyingErrorInvalidApiKey,
    ScimUnderlyingErrorInvalidPath,
    ScimUnderlyingErrorUserNotFound,
    ScimUnderlyingErrorGroupNotFound,
    ScimUnderlyingErrorMissingRequiredField,
    ScimUnderlyingErrorCantRemoveRequiredField,
    ScimUnderlyingErrorScimUserIdAlreadyTaken,
    ScimUnderlyingErrorInvalidBody,
    ScimUnderlyingErrorInvalidQueryField,
    ScimUnderlyingErrorInvalidPatchPath,
    ScimUnderlyingErrorInvalidPatchOperation,
    ScimUnderlyingErrorInvalidPatchValue,
    ScimUnderlyingErrorInvalidSchema,
    ScimUnderlyingErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'ScimUnderlyingError',
    'ScimUnderlyingErrorInvalidApiKey',
    'ScimUnderlyingErrorInvalidPath',
    'ScimUnderlyingErrorUserNotFound',
    'ScimUnderlyingErrorGroupNotFound',
    'ScimUnderlyingErrorMissingRequiredField',
    'ScimUnderlyingErrorCantRemoveRequiredField',
    'ScimUnderlyingErrorScimUserIdAlreadyTaken',
    'ScimUnderlyingErrorInvalidBody',
    'ScimUnderlyingErrorInvalidQueryField',
    'ScimUnderlyingErrorInvalidPatchPath',
    'ScimUnderlyingErrorInvalidPatchOperation',
    'ScimUnderlyingErrorInvalidPatchValue',
    'ScimUnderlyingErrorInvalidSchema',
    'ScimUnderlyingErrorUnexpectedError',
    'ScimUnderlyingErrorMissingRequiredFieldDetails',
    'ScimUnderlyingErrorCantRemoveRequiredFieldDetails',
    'ScimUnderlyingErrorScimUserIdAlreadyTakenDetails',
    'ScimUnderlyingErrorInvalidQueryFieldDetails',
    'ScimUnderlyingErrorInvalidPatchValueDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
