"""Auto-generated from TypeScript type: GetJwksResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .jwk_key import JwkKey


@dataclass
class GetJwksResponse:
    keys: List[JwkKey]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["keys"] = [item._to_request() for item in self.keys]
        return data