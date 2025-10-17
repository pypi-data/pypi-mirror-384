"""Auto-generated from TypeScript type: OptionalIdpInfoFromCustomerForEntra"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class OptionalIdpInfoFromCustomerForEntra:
    client_secret: Optional[str] = None
    uses_pkce: Optional[bool] = None
    tenant_id: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.client_secret is not None:
            data["clientSecret"] = self.client_secret
        if self.uses_pkce is not None:
            data["usesPkce"] = self.uses_pkce
        if self.tenant_id is not None:
            data["tenantId"] = self.tenant_id
        return data