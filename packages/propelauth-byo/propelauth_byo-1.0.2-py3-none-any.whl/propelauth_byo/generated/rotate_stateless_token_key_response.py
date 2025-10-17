"""Auto-generated from TypeScript type: RotateStatelessTokenKeyResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RotateStatelessTokenKeyResponse:
    new_key_id: str
    new_key_becomes_default_at: int
    existing_keys_expire_at: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["newKeyId"] = self.new_key_id
        data["newKeyBecomesDefaultAt"] = self.new_key_becomes_default_at
        data["existingKeysExpireAt"] = self.existing_keys_expire_at
        return data