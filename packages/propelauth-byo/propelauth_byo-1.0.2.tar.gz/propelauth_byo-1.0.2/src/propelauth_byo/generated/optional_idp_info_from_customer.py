"""Auto-generated from TypeScript type: OptionalIdpInfoFromCustomer"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class OptionalIdpInfoFromCustomerMicrosoftEntra:
    client_secret: Optional[str]
    uses_pkce: Optional[bool]
    tenant_id: Optional[str]
    idp_type: Literal["MicrosoftEntra"] = "MicrosoftEntra"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.client_secret is not None:
            data["clientSecret"] = self.client_secret
        if self.uses_pkce is not None:
            data["usesPkce"] = self.uses_pkce
        if self.tenant_id is not None:
            data["tenantId"] = self.tenant_id
        data["idpType"] = self.idp_type
        return data



@dataclass
class OptionalIdpInfoFromCustomerOkta:
    client_secret: Optional[str]
    uses_pkce: Optional[bool]
    sso_domain: Optional[str]
    idp_type: Literal["Okta"] = "Okta"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        if self.client_secret is not None:
            data["clientSecret"] = self.client_secret
        if self.uses_pkce is not None:
            data["usesPkce"] = self.uses_pkce
        if self.sso_domain is not None:
            data["ssoDomain"] = self.sso_domain
        data["idpType"] = self.idp_type
        return data



@dataclass
class OptionalIdpInfoFromCustomerGeneric:
    client_secret: Optional[str]
    uses_pkce: Optional[bool]
    auth_url: Optional[str]
    token_url: Optional[str]
    userinfo_url: Optional[str]
    idp_type: Literal["Generic"] = "Generic"

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
        data["idpType"] = self.idp_type
        return data




OptionalIdpInfoFromCustomer = Union[
    OptionalIdpInfoFromCustomerMicrosoftEntra,
    OptionalIdpInfoFromCustomerOkta,
    OptionalIdpInfoFromCustomerGeneric
]

# Export all types for client imports
__all__ = [
    'OptionalIdpInfoFromCustomer',
    'OptionalIdpInfoFromCustomerMicrosoftEntra',
    'OptionalIdpInfoFromCustomerOkta',
    'OptionalIdpInfoFromCustomerGeneric',
]

# Re-export UnexpectedErrorDetails if it was imported
