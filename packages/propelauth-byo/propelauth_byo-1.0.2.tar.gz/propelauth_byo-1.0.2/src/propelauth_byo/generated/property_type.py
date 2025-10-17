"""Auto-generated from TypeScript type: PropertyType"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class PropertyTypeString:
    data_type: Literal["String"] = "String"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeInteger:
    data_type: Literal["Integer"] = "Integer"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeFloat:
    data_type: Literal["Float"] = "Float"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeBoolean:
    data_type: Literal["Boolean"] = "Boolean"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeDate:
    data_type: Literal["Date"] = "Date"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeDateTime:
    data_type: Literal["DateTime"] = "DateTime"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeEnum:
    options: List[str]
    data_type: Literal["Enum"] = "Enum"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["options"] = self.options
        data["dataType"] = self.data_type
        return data



@dataclass
class PropertyTypeList:
    item_type: 'PropertyType'
    data_type: Literal["List"] = "List"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["itemType"] = self.item_type._to_request()
        data["dataType"] = self.data_type
        return data




PropertyType = Union[
    PropertyTypeString,
    PropertyTypeInteger,
    PropertyTypeFloat,
    PropertyTypeBoolean,
    PropertyTypeDate,
    PropertyTypeDateTime,
    PropertyTypeEnum,
    PropertyTypeList
]

# Export all types for client imports
__all__ = [
    'PropertyType',
    'PropertyTypeString',
    'PropertyTypeInteger',
    'PropertyTypeFloat',
    'PropertyTypeBoolean',
    'PropertyTypeDate',
    'PropertyTypeDateTime',
    'PropertyTypeEnum',
    'PropertyTypeList',
]

# Re-export UnexpectedErrorDetails if it was imported
