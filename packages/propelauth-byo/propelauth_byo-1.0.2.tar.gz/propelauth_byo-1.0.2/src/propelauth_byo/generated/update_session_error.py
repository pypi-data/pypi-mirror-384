"""Auto-generated from TypeScript type: UpdateSessionError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_tag_error import InvalidTagError
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class UpdateSessionErrorCannotModifyOnCreateOnlyTagsDetails:
    tag_names: List[str]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["tag_names"] = self.tag_names
        return data



@dataclass
class UpdateSessionErrorSessionNotFound:
    type: Literal["SessionNotFound"] = "SessionNotFound"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionErrorConflictingMetadataOptions:
    type: Literal["ConflictingMetadataOptions"] = "ConflictingMetadataOptions"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionErrorInvalidTagFormat:
    details: InvalidTagError
    type: Literal["InvalidTagFormat"] = "InvalidTagFormat"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionErrorCannotModifyOnCreateOnlyTags:
    details: UpdateSessionErrorCannotModifyOnCreateOnlyTagsDetails
    type: Literal["CannotModifyOnCreateOnlyTags"] = "CannotModifyOnCreateOnlyTags"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




UpdateSessionError = Union[
    UpdateSessionErrorSessionNotFound,
    UpdateSessionErrorConflictingMetadataOptions,
    UpdateSessionErrorInvalidTagFormat,
    UpdateSessionErrorCannotModifyOnCreateOnlyTags,
    UpdateSessionErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'UpdateSessionError',
    'UpdateSessionErrorSessionNotFound',
    'UpdateSessionErrorConflictingMetadataOptions',
    'UpdateSessionErrorInvalidTagFormat',
    'UpdateSessionErrorCannotModifyOnCreateOnlyTags',
    'UpdateSessionErrorUnexpectedError',
    'UpdateSessionErrorCannotModifyOnCreateOnlyTagsDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
