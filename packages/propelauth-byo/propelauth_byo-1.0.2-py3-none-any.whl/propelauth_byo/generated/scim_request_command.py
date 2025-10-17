"""Auto-generated from TypeScript type: ScimRequestCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .http_method import HttpMethod
from .serde_json.json_value import JsonValue


@dataclass
class ScimRequestCommand:
    method: HttpMethod
    path_and_query_params: str
    body: Optional[JsonValue] = None
    scim_api_key: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["method"] = self.method
        data["pathAndQueryParams"] = self.path_and_query_params
        if self.body is not None:
            data["body"] = self.body
        if self.scim_api_key is not None:
            data["scimApiKey"] = self.scim_api_key
        return data