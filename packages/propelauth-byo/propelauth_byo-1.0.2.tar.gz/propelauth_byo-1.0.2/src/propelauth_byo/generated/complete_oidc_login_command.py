"""Auto-generated from TypeScript type: CompleteOidcLoginCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class CompleteOidcLoginCommand:
    callback_path_and_query_params: str
    state_from_cookie: Optional[str] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["callbackPathAndQueryParams"] = self.callback_path_and_query_params
        if self.state_from_cookie is not None:
            data["stateFromCookie"] = self.state_from_cookie
        return data