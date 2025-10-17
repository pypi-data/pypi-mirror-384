"""Auto-generated from TypeScript type: UpdateSessionCommand"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from .serde_json.json_value import JsonValue


@dataclass
class UpdateSessionCommand:
    session_id: str
    tags_to_remove: Optional[List[str]] = None
    tags_to_add: Optional[List[str]] = None
    new_metadata: Optional[JsonValue] = None
    patch_metadata: Optional[JsonValue] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sessionId"] = self.session_id
        if self.tags_to_remove is not None:
            data["tagsToRemove"] = self.tags_to_remove
        if self.tags_to_add is not None:
            data["tagsToAdd"] = self.tags_to_add
        if self.new_metadata is not None:
            data["newMetadata"] = self.new_metadata
        if self.patch_metadata is not None:
            data["patchMetadata"] = self.patch_metadata
        return data