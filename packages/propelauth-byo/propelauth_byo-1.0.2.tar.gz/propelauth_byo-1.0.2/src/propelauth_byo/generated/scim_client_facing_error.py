"""Auto-generated from TypeScript type: ScimClientFacingError"""
from dataclasses import dataclass
from typing import Dict, Any
from .serde_json.json_value import JsonValue
from .scim_underlying_error import ScimUnderlyingError


@dataclass
class ScimClientFacingError:
    status_to_return: int
    body_to_return: JsonValue
    underlying_error: ScimUnderlyingError

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["statusToReturn"] = self.status_to_return
        data["bodyToReturn"] = self.body_to_return
        data["underlyingError"] = self.underlying_error._to_request()
        return data