"""Auto-generated from TypeScript type: PropertyParseError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .serde_json.json_value import JsonValue


@dataclass
class PropertyParseErrorPropertyMissing:
    output_field: str
    path: str
    error_type: Literal["property_missing"] = "property_missing"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["output_field"] = self.output_field
        data["path"] = self.path
        data["error_type"] = self.error_type
        return data



@dataclass
class PropertyParseErrorInvalidType:
    output_field: str
    path: str
    expected_type: str
    actual_value: JsonValue
    example: Optional[str]
    error_type: Literal["invalid_type"] = "invalid_type"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["output_field"] = self.output_field
        data["path"] = self.path
        data["expected_type"] = self.expected_type
        data["actual_value"] = self.actual_value
        if self.example is not None:
            data["example"] = self.example
        data["error_type"] = self.error_type
        return data



@dataclass
class PropertyParseErrorInvalidDateStructure:
    output_field: str
    path: str
    value: str
    expected_format: str
    example: str
    error_type: Literal["invalid_date_structure"] = "invalid_date_structure"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["output_field"] = self.output_field
        data["path"] = self.path
        data["value"] = self.value
        data["expected_format"] = self.expected_format
        data["example"] = self.example
        data["error_type"] = self.error_type
        return data



@dataclass
class PropertyParseErrorInvalidDateTimeStructure:
    output_field: str
    path: str
    value: str
    expected_format: str
    example: str
    error_type: Literal["invalid_date_time_structure"] = "invalid_date_time_structure"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["output_field"] = self.output_field
        data["path"] = self.path
        data["value"] = self.value
        data["expected_format"] = self.expected_format
        data["example"] = self.example
        data["error_type"] = self.error_type
        return data



@dataclass
class PropertyParseErrorInvalidEnumValue:
    output_field: str
    path: str
    value: str
    allowed_values: List[str]
    error_type: Literal["invalid_enum_value"] = "invalid_enum_value"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["output_field"] = self.output_field
        data["path"] = self.path
        data["value"] = self.value
        data["allowed_values"] = self.allowed_values
        data["error_type"] = self.error_type
        return data




PropertyParseError = Union[
    PropertyParseErrorPropertyMissing,
    PropertyParseErrorInvalidType,
    PropertyParseErrorInvalidDateStructure,
    PropertyParseErrorInvalidDateTimeStructure,
    PropertyParseErrorInvalidEnumValue
]

# Export all types for client imports
__all__ = [
    'PropertyParseError',
    'PropertyParseErrorPropertyMissing',
    'PropertyParseErrorInvalidType',
    'PropertyParseErrorInvalidDateStructure',
    'PropertyParseErrorInvalidDateTimeStructure',
    'PropertyParseErrorInvalidEnumValue',
]

# Re-export UnexpectedErrorDetails if it was imported
