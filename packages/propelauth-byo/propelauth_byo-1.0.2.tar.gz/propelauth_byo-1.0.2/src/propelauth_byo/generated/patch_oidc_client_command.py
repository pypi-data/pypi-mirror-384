"""Auto-generated from TypeScript type: PatchOidcClientCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .optional_idp_info_from_customer import OptionalIdpInfoFromCustomer
from .scim_matching_definition import ScimMatchingDefinition


@dataclass
class PatchOidcClientCommandOidcClientId:
    oidc_client_id: str
    idp_info_from_customer: Optional[OptionalIdpInfoFromCustomer]
    display_name: Optional[str]
    email_domain_allowlist: Optional[List[str]]
    redirect_url: Optional[str]
    additional_scopes: Optional[List[str]]
    scim_matching_definition: Optional[ScimMatchingDefinition]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["oidcClientId"] = self.oidc_client_id
        if self.idp_info_from_customer is not None:
            data["idpInfoFromCustomer"] = self.idp_info_from_customer._to_request()
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.email_domain_allowlist is not None:
            data["emailDomainAllowlist"] = self.email_domain_allowlist
        if self.redirect_url is not None:
            data["redirectUrl"] = self.redirect_url
        if self.additional_scopes is not None:
            data["additionalScopes"] = self.additional_scopes
        if self.scim_matching_definition is not None:
            data["scimMatchingDefinition"] = self.scim_matching_definition._to_request()
        return data



@dataclass
class PatchOidcClientCommandCustomerId:
    customer_id: str
    idp_info_from_customer: Optional[OptionalIdpInfoFromCustomer]
    display_name: Optional[str]
    email_domain_allowlist: Optional[List[str]]
    redirect_url: Optional[str]
    additional_scopes: Optional[List[str]]
    scim_matching_definition: Optional[ScimMatchingDefinition]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        if self.idp_info_from_customer is not None:
            data["idpInfoFromCustomer"] = self.idp_info_from_customer._to_request()
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.email_domain_allowlist is not None:
            data["emailDomainAllowlist"] = self.email_domain_allowlist
        if self.redirect_url is not None:
            data["redirectUrl"] = self.redirect_url
        if self.additional_scopes is not None:
            data["additionalScopes"] = self.additional_scopes
        if self.scim_matching_definition is not None:
            data["scimMatchingDefinition"] = self.scim_matching_definition._to_request()
        return data




PatchOidcClientCommand = Union[
    PatchOidcClientCommandOidcClientId,
    PatchOidcClientCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'PatchOidcClientCommand',
    'PatchOidcClientCommandOidcClientId',
    'PatchOidcClientCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
