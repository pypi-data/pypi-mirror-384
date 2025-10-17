"""Auto-generated from TypeScript type: ScimMatchingDefinition"""
from dataclasses import dataclass
from typing import Dict, Any
from .scim_user_matching_strategy import ScimUserMatchingStrategy


@dataclass
class ScimMatchingDefinition:
    strategy: ScimUserMatchingStrategy

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["strategy"] = self.strategy
        return data