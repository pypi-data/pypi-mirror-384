"""Auto-generated from TypeScript type: CreateStatelessTokenCommand"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .serde_json.json_value import JsonValue


@dataclass
class CreateStatelessTokenCommand:
    user_id: str
    session_id: Optional[str] = None
    custom_claims: Optional[JsonValue] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    not_before_unixtime: Optional[int] = None
    lifetime_secs: Optional[int] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        if self.session_id is not None:
            data["sessionId"] = self.session_id
        if self.custom_claims is not None:
            data["customClaims"] = self.custom_claims
        if self.issuer is not None:
            data["issuer"] = self.issuer
        if self.audience is not None:
            data["audience"] = self.audience
        if self.not_before_unixtime is not None:
            data["notBeforeUnixtime"] = self.not_before_unixtime
        if self.lifetime_secs is not None:
            data["lifetimeSecs"] = self.lifetime_secs
        return data