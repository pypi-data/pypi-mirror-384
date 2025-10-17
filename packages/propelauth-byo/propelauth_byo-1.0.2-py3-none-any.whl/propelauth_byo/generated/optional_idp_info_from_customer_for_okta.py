"""Auto-generated from TypeScript type: OptionalIdpInfoFromCustomerForOkta"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class OptionalIdpInfoFromCustomerForOkta:
    client_secret: Optional[str] = None
    uses_pkce: Optional[bool] = None
    sso_domain: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.client_secret is not None:
            data["clientSecret"] = self.client_secret
        if self.uses_pkce is not None:
            data["usesPkce"] = self.uses_pkce
        if self.sso_domain is not None:
            data["ssoDomain"] = self.sso_domain
        return data