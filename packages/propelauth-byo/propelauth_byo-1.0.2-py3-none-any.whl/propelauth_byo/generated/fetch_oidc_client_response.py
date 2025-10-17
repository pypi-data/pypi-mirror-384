"""Auto-generated from TypeScript type: FetchOidcClientResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .idp_info_from_customer_response import IdpInfoFromCustomerResponse
from .fetch_scim_connection_response import FetchScimConnectionResponse
from .scim_matching_definition import ScimMatchingDefinition


@dataclass
class FetchOidcClientResponse:
    idp_info_from_customer: IdpInfoFromCustomerResponse
    customer_id: str
    redirect_url: str
    email_domain_allowlist: List[str]
    additional_scopes: List[str]
    display_name: Optional[str] = None
    scim_connection: Optional[FetchScimConnectionResponse] = None
    scim_matching_definition: Optional[ScimMatchingDefinition] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["idpInfoFromCustomer"] = self.idp_info_from_customer._to_request()
        data["customerId"] = self.customer_id
        data["redirectUrl"] = self.redirect_url
        data["emailDomainAllowlist"] = self.email_domain_allowlist
        data["additionalScopes"] = self.additional_scopes
        if self.display_name is not None:
            data["displayName"] = self.display_name
        if self.scim_connection is not None:
            data["scimConnection"] = self.scim_connection._to_request()
        if self.scim_matching_definition is not None:
            data["scimMatchingDefinition"] = self.scim_matching_definition._to_request()
        return data