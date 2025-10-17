"""Auto-generated from TypeScript type: IdpInfoFromCustomerResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class IdpInfoFromCustomerResponseMicrosoftEntra:
    client_id: str
    uses_pkce: bool
    tenant_id: str
    idp_type: Literal["MicrosoftEntra"] = "MicrosoftEntra"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["clientId"] = self.client_id
        data["usesPkce"] = self.uses_pkce
        data["tenantId"] = self.tenant_id
        data["idpType"] = self.idp_type
        return data



@dataclass
class IdpInfoFromCustomerResponseOkta:
    client_id: str
    uses_pkce: bool
    sso_domain: str
    idp_type: Literal["Okta"] = "Okta"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["clientId"] = self.client_id
        data["usesPkce"] = self.uses_pkce
        data["ssoDomain"] = self.sso_domain
        data["idpType"] = self.idp_type
        return data



@dataclass
class IdpInfoFromCustomerResponseGeneric:
    client_id: str
    uses_pkce: bool
    auth_url: str
    token_url: str
    userinfo_url: str
    idp_type: Literal["Generic"] = "Generic"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["clientId"] = self.client_id
        data["usesPkce"] = self.uses_pkce
        data["authUrl"] = self.auth_url
        data["tokenUrl"] = self.token_url
        data["userinfoUrl"] = self.userinfo_url
        data["idpType"] = self.idp_type
        return data




IdpInfoFromCustomerResponse = Union[
    IdpInfoFromCustomerResponseMicrosoftEntra,
    IdpInfoFromCustomerResponseOkta,
    IdpInfoFromCustomerResponseGeneric
]

# Export all types for client imports
__all__ = [
    'IdpInfoFromCustomerResponse',
    'IdpInfoFromCustomerResponseMicrosoftEntra',
    'IdpInfoFromCustomerResponseOkta',
    'IdpInfoFromCustomerResponseGeneric',
]

# Re-export UnexpectedErrorDetails if it was imported
