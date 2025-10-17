"""Auto-generated from TypeScript type: CompletedScimRequestResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .serde_json.json_value import JsonValue


@dataclass
class CompletedScimRequestResponse:
    connection_id: str
    response_http_code: int
    response_data: Optional[JsonValue] = None
    affected_user_ids: Optional[List[str]] = None

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["responseHttpCode"] = self.response_http_code
        if self.response_data is not None:
            data["responseData"] = self.response_data
        if self.affected_user_ids is not None:
            data["affectedUserIds"] = self.affected_user_ids
        return data