"""Auto-generated from TypeScript type: IdentityProvider"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class IdentityProviderMicrosoftEntra:
    tenant_id: str
    idp_type: Literal["MicrosoftEntra"] = "MicrosoftEntra"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["tenantId"] = self.tenant_id
        data["idpType"] = self.idp_type
        return data



@dataclass
class IdentityProviderOkta:
    sso_domain: str
    idp_type: Literal["Okta"] = "Okta"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["ssoDomain"] = self.sso_domain
        data["idpType"] = self.idp_type
        return data



@dataclass
class IdentityProviderGeneric:
    auth_url: str
    token_url: str
    userinfo_url: str
    idp_type: Literal["Generic"] = "Generic"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["authUrl"] = self.auth_url
        data["tokenUrl"] = self.token_url
        data["userinfoUrl"] = self.userinfo_url
        data["idpType"] = self.idp_type
        return data




IdentityProvider = Union[
    IdentityProviderMicrosoftEntra,
    IdentityProviderOkta,
    IdentityProviderGeneric
]

# Export all types for client imports
__all__ = [
    'IdentityProvider',
    'IdentityProviderMicrosoftEntra',
    'IdentityProviderOkta',
    'IdentityProviderGeneric',
]

# Re-export UnexpectedErrorDetails if it was imported
