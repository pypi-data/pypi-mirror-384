"""Auto-generated from TypeScript type: StartPasskeyRegistrationCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class StartPasskeyRegistrationCommand:
    user_id: str
    email_or_username: str
    user_display_name: Optional[str] = None
    passkey_display_name: Optional[str] = None
    additional_allowed_origin: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        data["emailOrUsername"] = self.email_or_username
        if self.user_display_name is not None:
            data["userDisplayName"] = self.user_display_name
        if self.passkey_display_name is not None:
            data["passkeyDisplayName"] = self.passkey_display_name
        if self.additional_allowed_origin is not None:
            data["additionalAllowedOrigin"] = self.additional_allowed_origin
        return data