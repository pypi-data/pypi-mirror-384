"""Auto-generated from TypeScript type: RotateStatelessTokenKeyCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RotateStatelessTokenKeyCommand:
    secs_before_new_key_becomes_default: int
    secs_before_existing_keys_are_deactivated: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["secsBeforeNewKeyBecomesDefault"] = self.secs_before_new_key_becomes_default
        data["secsBeforeExistingKeysAreDeactivated"] = self.secs_before_existing_keys_are_deactivated
        return data