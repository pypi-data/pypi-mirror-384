"""Auto-generated from TypeScript type: ScimUserMappingConfig"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .scim_user_mapping_field_definition import ScimUserMappingFieldDefinition


@dataclass
class ScimUserMappingConfig:
    user_schema: List[ScimUserMappingFieldDefinition]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userSchema"] = [item._to_request() for item in self.user_schema]
        return data