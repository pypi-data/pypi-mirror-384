"""Auto-generated from TypeScript type: CreateOidcClientCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .idp_info_from_customer import IdpInfoFromCustomer
from .scim_matching_definition import ScimMatchingDefinition


@dataclass
class CreateOidcClientCommand:
    idp_info_from_customer: IdpInfoFromCustomer
    customer_id: str
    redirect_url: str
    display_name: Optional[str] = None
    additional_scopes: Optional[List[str]] = None
    scim_matching_definition: Optional[ScimMatchingDefinition] = None
    email_domain_allowlist: Optional[List[str]] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["idpInfoFromCustomer"] = self.idp_info_from_customer._to_request()
        data["customerId"] = self.customer_id
        data["redirectUrl"] = self.redirect_url
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.additional_scopes is not None:
            data["additionalScopes"] = self.additional_scopes
        if self.scim_matching_definition is not None:
            data["scimMatchingDefinition"] = self.scim_matching_definition._to_request()
        if self.email_domain_allowlist is not None:
            data["emailDomainAllowlist"] = self.email_domain_allowlist
        return data