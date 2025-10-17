"""Auto-generated from TypeScript type: InitiateOidcLoginResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InitiateOidcLoginResponse:
    send_user_to_idp_url: str
    state_for_cookie: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["sendUserToIdpUrl"] = self.send_user_to_idp_url
        data["stateForCookie"] = self.state_for_cookie
        return data