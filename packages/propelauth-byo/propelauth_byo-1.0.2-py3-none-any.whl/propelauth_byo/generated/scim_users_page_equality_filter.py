"""Auto-generated from TypeScript type: ScimUsersPageEqualityFilter"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class ScimUsersPageEqualityFilterUserName:
    user_name: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userName"] = self.user_name
        return data



@dataclass
class ScimUsersPageEqualityFilterExternalId:
    external_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["externalId"] = self.external_id
        return data



@dataclass
class ScimUsersPageEqualityFilterPrimaryEmail:
    primary_email: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["primaryEmail"] = self.primary_email
        return data



@dataclass
class ScimUsersPageEqualityFilterUserId:
    user_id: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["userId"] = self.user_id
        return data




ScimUsersPageEqualityFilter = Union[
    ScimUsersPageEqualityFilterUserName,
    ScimUsersPageEqualityFilterExternalId,
    ScimUsersPageEqualityFilterPrimaryEmail,
    ScimUsersPageEqualityFilterUserId
]

# Export all types for client imports
__all__ = [
    'ScimUsersPageEqualityFilter',
    'ScimUsersPageEqualityFilterUserName',
    'ScimUsersPageEqualityFilterExternalId',
    'ScimUsersPageEqualityFilterPrimaryEmail',
    'ScimUsersPageEqualityFilterUserId',
]

# Re-export UnexpectedErrorDetails if it was imported
