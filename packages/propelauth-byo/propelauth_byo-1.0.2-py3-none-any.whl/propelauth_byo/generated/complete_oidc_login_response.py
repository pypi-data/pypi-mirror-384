"""Auto-generated from TypeScript type: CompleteOidcLoginResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .serde_json.json_value import JsonValue
from .complete_scim_user_response import CompleteScimUserResponse


@dataclass
class CompleteOidcLoginResponse:
    client_id: str
    customer_id: str
    oidc_user_id: str
    email_verified: bool
    data_from_sso: JsonValue
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    scim_user: Optional[CompleteScimUserResponse] = None
    post_login_redirect_url: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["clientId"] = self.client_id
        data["customerId"] = self.customer_id
        data["oidcUserId"] = self.oidc_user_id
        data["emailVerified"] = self.email_verified
        data["dataFromSso"] = self.data_from_sso
        if self.email is not None:
            data["email"] = self.email
        if self.preferred_username is not None:
            data["preferredUsername"] = self.preferred_username
        if self.scim_user is not None:
            data["scimUser"] = self.scim_user._to_request()
        if self.post_login_redirect_url is not None:
            data["postLoginRedirectUrl"] = self.post_login_redirect_url
        return data