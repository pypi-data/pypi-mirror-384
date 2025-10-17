"""Auto-generated from TypeScript type: InitiateOidcLoginCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class InitiateOidcLoginCommandOidcClientId:
    oidc_client_id: str
    post_login_redirect_url: Optional[str]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["oidcClientId"] = self.oidc_client_id
        if self.post_login_redirect_url is not None:
            data["postLoginRedirectUrl"] = self.post_login_redirect_url
        return data



@dataclass
class InitiateOidcLoginCommandCustomerId:
    customer_id: str
    post_login_redirect_url: Optional[str]

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["customerId"] = self.customer_id
        if self.post_login_redirect_url is not None:
            data["postLoginRedirectUrl"] = self.post_login_redirect_url
        return data




InitiateOidcLoginCommand = Union[
    InitiateOidcLoginCommandOidcClientId,
    InitiateOidcLoginCommandCustomerId
]

# Export all types for client imports
__all__ = [
    'InitiateOidcLoginCommand',
    'InitiateOidcLoginCommandOidcClientId',
    'InitiateOidcLoginCommandCustomerId',
]

# Re-export UnexpectedErrorDetails if it was imported
