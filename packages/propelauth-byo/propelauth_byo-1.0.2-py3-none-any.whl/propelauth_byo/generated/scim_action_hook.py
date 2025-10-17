"""Auto-generated from TypeScript type: ScimActionHook"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .serde_json.json_value import JsonValue


@dataclass
class ScimActionHookLinkUser:
    commit_id: str
    user_name: str
    parsed_user_data: JsonValue
    active: bool
    primary_email: Optional[str]
    sso_user_subject: Optional[str]
    action: Literal["LinkUser"] = "LinkUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["commitId"] = self.commit_id
        data["userName"] = self.user_name
        data["parsedUserData"] = self.parsed_user_data
        data["active"] = self.active
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        if self.sso_user_subject is not None:
            data["ssoUserSubject"] = self.sso_user_subject
        data["action"] = self.action
        return data



@dataclass
class ScimActionHookDisableUser:
    commit_id: str
    user_id: str
    parsed_user_data: JsonValue
    primary_email: Optional[str]
    action: Literal["DisableUser"] = "DisableUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        data["parsedUserData"] = self.parsed_user_data
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        data["action"] = self.action
        return data



@dataclass
class ScimActionHookEnableUser:
    commit_id: str
    user_id: str
    parsed_user_data: JsonValue
    primary_email: Optional[str]
    action: Literal["EnableUser"] = "EnableUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        data["parsedUserData"] = self.parsed_user_data
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        data["action"] = self.action
        return data



@dataclass
class ScimActionHookDeleteUser:
    commit_id: str
    user_id: str
    parsed_user_data: JsonValue
    primary_email: Optional[str]
    action: Literal["DeleteUser"] = "DeleteUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["commitId"] = self.commit_id
        data["userId"] = self.user_id
        data["parsedUserData"] = self.parsed_user_data
        if self.primary_email is not None:
            data["primaryEmail"] = self.primary_email
        data["action"] = self.action
        return data




ScimActionHook = Union[
    ScimActionHookLinkUser,
    ScimActionHookDisableUser,
    ScimActionHookEnableUser,
    ScimActionHookDeleteUser
]

# Export all types for client imports
__all__ = [
    'ScimActionHook',
    'ScimActionHookLinkUser',
    'ScimActionHookDisableUser',
    'ScimActionHookEnableUser',
    'ScimActionHookDeleteUser',
]

# Re-export UnexpectedErrorDetails if it was imported
