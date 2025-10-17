"""Auto-generated from TypeScript type: UpdateSessionsError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .invalid_tag_error import InvalidTagError
from .unexpected_error_details import UnexpectedErrorDetails

@dataclass
class UpdateSessionsErrorCannotModifyOnCreateOnlyTagsDetails:
    tag_names: List[str]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["tag_names"] = self.tag_names
        return data



@dataclass
class UpdateSessionsErrorConflictingMetadataOptions:
    type: Literal["ConflictingMetadataOptions"] = "ConflictingMetadataOptions"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionsErrorInvalidTagFormat:
    details: InvalidTagError
    type: Literal["InvalidTagFormat"] = "InvalidTagFormat"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionsErrorCannotModifyOnCreateOnlyTags:
    details: UpdateSessionsErrorCannotModifyOnCreateOnlyTagsDetails
    type: Literal["CannotModifyOnCreateOnlyTags"] = "CannotModifyOnCreateOnlyTags"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details._to_request()
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionsErrorUpdatingTooManySessionsAtOnce:
    type: Literal["UpdatingTooManySessionsAtOnce"] = "UpdatingTooManySessionsAtOnce"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["type"] = self.type
        return data



@dataclass
class UpdateSessionsErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




UpdateSessionsError = Union[
    UpdateSessionsErrorConflictingMetadataOptions,
    UpdateSessionsErrorInvalidTagFormat,
    UpdateSessionsErrorCannotModifyOnCreateOnlyTags,
    UpdateSessionsErrorUpdatingTooManySessionsAtOnce,
    UpdateSessionsErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'UpdateSessionsError',
    'UpdateSessionsErrorConflictingMetadataOptions',
    'UpdateSessionsErrorInvalidTagFormat',
    'UpdateSessionsErrorCannotModifyOnCreateOnlyTags',
    'UpdateSessionsErrorUpdatingTooManySessionsAtOnce',
    'UpdateSessionsErrorUnexpectedError',
    'UpdateSessionsErrorCannotModifyOnCreateOnlyTagsDetails',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
