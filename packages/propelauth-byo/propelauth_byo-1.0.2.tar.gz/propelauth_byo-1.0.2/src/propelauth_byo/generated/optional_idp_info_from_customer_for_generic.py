"""Auto-generated from TypeScript type: OptionalIdpInfoFromCustomerForGeneric"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class OptionalIdpInfoFromCustomerForGeneric:
    client_secret: Optional[str] = None
    uses_pkce: Optional[bool] = None
    auth_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.client_secret is not None:
            data["clientSecret"] = self.client_secret
        if self.uses_pkce is not None:
            data["usesPkce"] = self.uses_pkce
        if self.auth_url is not None:
            data["authUrl"] = self.auth_url
        if self.token_url is not None:
            data["tokenUrl"] = self.token_url
        if self.userinfo_url is not None:
            data["userinfoUrl"] = self.userinfo_url
        return data