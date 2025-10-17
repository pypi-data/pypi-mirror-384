"""Auto-generated from TypeScript type: DeleteOidcClientResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DeleteOidcClientResponse:
    pass

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        return data