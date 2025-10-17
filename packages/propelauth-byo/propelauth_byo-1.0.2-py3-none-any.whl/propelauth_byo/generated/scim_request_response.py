"""Auto-generated from TypeScript type: ScimRequestResponse"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .serde_json.json_value import JsonValue


@dataclass
class ScimRequestResponseCompleted:
    connection_id: str
    response_http_code: int
    response_data: Optional[JsonValue]
    affected_user_ids: Optional[List[str]]
    status: Literal["Completed"] = "Completed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["responseHttpCode"] = self.response_http_code
        if self.response_data is not None:
            data["responseData"] = self.response_data
        if self.affected_user_ids is not None:
            data["affectedUserIds"] = self.affected_user_ids
        data["status"] = self.status
        return data



@dataclass
class ScimRequestResponseActionRequiredLinkUser:
    connection_id: str
    commit_id: str
    user_name: str
    parsed_user_data: JsonValue
    active: bool
    primary_email: Optional[str]
    sso_user_subject: Optional[str]
    status: Literal["ActionRequired"] = "ActionRequired"
    action: Literal["LinkUser"] = "LinkUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["commitId"] = self.commit_id
        data["userName"] = self.user_name
        data["parsedUserData"] = self.parsed_user_data
        data["active"] = self.active
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        if self.sso_user_subject is not None:
            data["ssoUserSubject"] = self.sso_user_subject
        data["status"] = self.status
        data["action"] = self.action
        return data



@dataclass
class ScimRequestResponseActionRequiredDisableUser:
    connection_id: str
    commit_id: str
    user_id: str
    parsed_user_data: JsonValue
    primary_email: Optional[str]
    status: Literal["ActionRequired"] = "ActionRequired"
    action: Literal["DisableUser"] = "DisableUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        data["parsedUserData"] = self.parsed_user_data
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        data["status"] = self.status
        data["action"] = self.action
        return data



@dataclass
class ScimRequestResponseActionRequiredEnableUser:
    connection_id: str
    commit_id: str
    user_id: str
    parsed_user_data: JsonValue
    primary_email: Optional[str]
    status: Literal["ActionRequired"] = "ActionRequired"
    action: Literal["EnableUser"] = "EnableUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        data["parsedUserData"] = self.parsed_user_data
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        data["status"] = self.status
        data["action"] = self.action
        return data



@dataclass
class ScimRequestResponseActionRequiredDeleteUser:
    connection_id: str
    commit_id: str
    user_id: str
    parsed_user_data: JsonValue
    primary_email: Optional[str]
    status: Literal["ActionRequired"] = "ActionRequired"
    action: Literal["DeleteUser"] = "DeleteUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["connectionId"] = self.connection_id
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        data["parsedUserData"] = self.parsed_user_data
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        data["status"] = self.status
        data["action"] = self.action
        return data




ScimRequestResponse = Union[
    ScimRequestResponseCompleted,
    ScimRequestResponseActionRequiredLinkUser,
    ScimRequestResponseActionRequiredDisableUser,
    ScimRequestResponseActionRequiredEnableUser,
    ScimRequestResponseActionRequiredDeleteUser
]

# Export all types for client imports
__all__ = [
    'ScimRequestResponse',
    'ScimRequestResponseCompleted',
    'ScimRequestResponseActionRequiredLinkUser',
    'ScimRequestResponseActionRequiredDisableUser',
    'ScimRequestResponseActionRequiredEnableUser',
    'ScimRequestResponseActionRequiredDeleteUser',
]

# Re-export UnexpectedErrorDetails if it was imported
