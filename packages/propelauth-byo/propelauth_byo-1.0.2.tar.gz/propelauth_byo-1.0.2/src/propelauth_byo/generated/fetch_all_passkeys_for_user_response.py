"""Auto-generated from TypeScript type: FetchAllPasskeysForUserResponse"""
from dataclasses import dataclass
from typing import Dict, Any, List
from .passkey_info import PasskeyInfo


@dataclass
class FetchAllPasskeysForUserResponse:
    passkeys: List[PasskeyInfo]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["passkeys"] = [item._to_request() for item in self.passkeys]
        return data