"""Auto-generated from TypeScript type: ScimUserMappingFieldDefinition"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .property_type import PropertyType
from .serde_json.json_value import JsonValue


@dataclass
class ScimUserMappingFieldDefinition:
    output_field: str
    input_path: str
    fallback_input_paths: List[str]
    property_type: PropertyType
    display_name: str
    warn_if_missing: bool
    description: Optional[str] = None
    default_value: Optional[JsonValue] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["outputField"] = self.output_field
        data["inputPath"] = self.input_path
        data["fallbackInputPaths"] = self.fallback_input_paths
        data["propertyType"] = self.property_type._to_request()
        data["displayName"] = self.display_name
        data["warnIfMissing"] = self.warn_if_missing
        if self.description is not None:
            data["description"] = self.description
        if self.default_value is not None:
            data["defaultValue"] = self.default_value
        return data