"""Auto-generated from TypeScript type: Command"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .ping_command import PingCommand
from .start_passkey_registration_command import StartPasskeyRegistrationCommand
from .finish_passkey_registration_command import FinishPasskeyRegistrationCommand
from .start_passkey_authentication_command import StartPasskeyAuthenticationCommand
from .finish_passkey_authentication_command import FinishPasskeyAuthenticationCommand
from .fetch_all_passkeys_for_user_command import FetchAllPasskeysForUserCommand
from .deregister_passkey_command import DeregisterPasskeyCommand
from .deregister_all_passkeys_for_user_command import DeregisterAllPasskeysForUserCommand
from .create_device_challenge_command import CreateDeviceChallengeCommand
from .create_session_command import CreateSessionCommand
from .register_device_command import RegisterDeviceCommand
from .create_stateless_token_command import CreateStatelessTokenCommand
from .get_jwks_command import GetJwksCommand
from .rotate_stateless_token_key_command import RotateStatelessTokenKeyCommand
from .invalidate_session_by_token_command import InvalidateSessionByTokenCommand
from .invalidate_session_by_id_command import InvalidateSessionByIdCommand
from .invalidate_all_sessions_for_user_command import InvalidateAllSessionsForUserCommand
from .invalidate_all_sessions_for_user_except_one_command import InvalidateAllSessionsForUserExceptOneCommand
from .fetch_all_sessions_for_user_command import FetchAllSessionsForUserCommand
from .fetch_all_sessions_command import FetchAllSessionsCommand
from .fetch_session_by_id_command import FetchSessionByIdCommand
from .update_session_command import UpdateSessionCommand
from .update_sessions_command import UpdateSessionsCommand
from .validate_session_command import ValidateSessionCommand
from .validate_and_refresh_session_command import ValidateAndRefreshSessionCommand
from .create_impersonation_session_command import CreateImpersonationSessionCommand
from .validate_impersonation_session_command import ValidateImpersonationSessionCommand
from .fetch_impersonation_session_by_id_command import FetchImpersonationSessionByIdCommand
from .fetch_all_impersonation_sessions_for_employee_command import FetchAllImpersonationSessionsForEmployeeCommand
from .fetch_all_impersonation_sessions_for_user_command import FetchAllImpersonationSessionsForUserCommand
from .fetch_all_active_impersonation_sessions_command import FetchAllActiveImpersonationSessionsCommand
from .invalidate_impersonation_session_by_id_command import InvalidateImpersonationSessionByIdCommand
from .invalidate_impersonation_session_by_token_command import InvalidateImpersonationSessionByTokenCommand
from .invalidate_all_impersonation_sessions_for_employee_command import InvalidateAllImpersonationSessionsForEmployeeCommand
from .invalidate_all_impersonation_sessions_for_user_command import InvalidateAllImpersonationSessionsForUserCommand
from .scim_request_command import ScimRequestCommand
from .link_scim_user_command import LinkScimUserCommand
from .commit_scim_user_change_command import CommitScimUserChangeCommand
from .create_scim_connection_command import CreateScimConnectionCommand
from .fetch_scim_connection_command import FetchScimConnectionCommand
from .patch_scim_connection_command import PatchScimConnectionCommand
from .reset_scim_api_key_command import ResetScimApiKeyCommand
from .delete_scim_connection_command import DeleteScimConnectionCommand
from .get_scim_users_command import GetScimUsersCommand
from .get_scim_user_command import GetScimUserCommand
from .create_oidc_client_command import CreateOidcClientCommand
from .fetch_oidc_client_command import FetchOidcClientCommand
from .patch_oidc_client_command import PatchOidcClientCommand
from .delete_oidc_client_command import DeleteOidcClientCommand
from .initiate_oidc_login_command import InitiateOidcLoginCommand
from .complete_oidc_login_command import CompleteOidcLoginCommand


@dataclass
class CommandPing:
    data: PingCommand
    command: Literal["Ping"] = "Ping"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandStartPasskeyRegistration:
    data: StartPasskeyRegistrationCommand
    command: Literal["StartPasskeyRegistration"] = "StartPasskeyRegistration"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFinishPasskeyRegistration:
    data: FinishPasskeyRegistrationCommand
    command: Literal["FinishPasskeyRegistration"] = "FinishPasskeyRegistration"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandStartPasskeyAuthentication:
    data: StartPasskeyAuthenticationCommand
    command: Literal["StartPasskeyAuthentication"] = "StartPasskeyAuthentication"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFinishPasskeyAuthentication:
    data: FinishPasskeyAuthenticationCommand
    command: Literal["FinishPasskeyAuthentication"] = "FinishPasskeyAuthentication"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchAllPasskeysForUser:
    data: FetchAllPasskeysForUserCommand
    command: Literal["FetchAllPasskeysForUser"] = "FetchAllPasskeysForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandDeregisterPasskey:
    data: DeregisterPasskeyCommand
    command: Literal["DeregisterPasskey"] = "DeregisterPasskey"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandDeregisterAllPasskeysForUser:
    data: DeregisterAllPasskeysForUserCommand
    command: Literal["DeregisterAllPasskeysForUser"] = "DeregisterAllPasskeysForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCreateDeviceChallenge:
    data: CreateDeviceChallengeCommand
    command: Literal["CreateDeviceChallenge"] = "CreateDeviceChallenge"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCreateSession:
    data: CreateSessionCommand
    command: Literal["CreateSession"] = "CreateSession"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandRegisterDevice:
    data: RegisterDeviceCommand
    command: Literal["RegisterDevice"] = "RegisterDevice"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCreateStatelessToken:
    data: CreateStatelessTokenCommand
    command: Literal["CreateStatelessToken"] = "CreateStatelessToken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandGetJwks:
    data: GetJwksCommand
    command: Literal["GetJwks"] = "GetJwks"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandRotateStatelessTokenKey:
    data: RotateStatelessTokenKeyCommand
    command: Literal["RotateStatelessTokenKey"] = "RotateStatelessTokenKey"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateSessionByToken:
    data: InvalidateSessionByTokenCommand
    command: Literal["InvalidateSessionByToken"] = "InvalidateSessionByToken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateSessionById:
    data: InvalidateSessionByIdCommand
    command: Literal["InvalidateSessionById"] = "InvalidateSessionById"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateAllSessionsForUser:
    data: InvalidateAllSessionsForUserCommand
    command: Literal["InvalidateAllSessionsForUser"] = "InvalidateAllSessionsForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateAllSessionsForUserExceptOne:
    data: InvalidateAllSessionsForUserExceptOneCommand
    command: Literal["InvalidateAllSessionsForUserExceptOne"] = "InvalidateAllSessionsForUserExceptOne"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchAllSessionsForUser:
    data: FetchAllSessionsForUserCommand
    command: Literal["FetchAllSessionsForUser"] = "FetchAllSessionsForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchAllSessions:
    data: FetchAllSessionsCommand
    command: Literal["FetchAllSessions"] = "FetchAllSessions"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchSessionById:
    data: FetchSessionByIdCommand
    command: Literal["FetchSessionById"] = "FetchSessionById"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandUpdateSession:
    data: UpdateSessionCommand
    command: Literal["UpdateSession"] = "UpdateSession"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandUpdateSessions:
    data: UpdateSessionsCommand
    command: Literal["UpdateSessions"] = "UpdateSessions"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandValidateSession:
    data: ValidateSessionCommand
    command: Literal["ValidateSession"] = "ValidateSession"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandValidateAndRefreshSession:
    data: ValidateAndRefreshSessionCommand
    command: Literal["ValidateAndRefreshSession"] = "ValidateAndRefreshSession"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCreateImpersonationSession:
    data: CreateImpersonationSessionCommand
    command: Literal["CreateImpersonationSession"] = "CreateImpersonationSession"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandValidateImpersonationSession:
    data: ValidateImpersonationSessionCommand
    command: Literal["ValidateImpersonationSession"] = "ValidateImpersonationSession"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchImpersonationSessionById:
    data: FetchImpersonationSessionByIdCommand
    command: Literal["FetchImpersonationSessionById"] = "FetchImpersonationSessionById"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchAllImpersonationSessionsForEmployee:
    data: FetchAllImpersonationSessionsForEmployeeCommand
    command: Literal["FetchAllImpersonationSessionsForEmployee"] = "FetchAllImpersonationSessionsForEmployee"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchAllImpersonationSessionsForUser:
    data: FetchAllImpersonationSessionsForUserCommand
    command: Literal["FetchAllImpersonationSessionsForUser"] = "FetchAllImpersonationSessionsForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchAllActiveImpersonationSessions:
    data: FetchAllActiveImpersonationSessionsCommand
    command: Literal["FetchAllActiveImpersonationSessions"] = "FetchAllActiveImpersonationSessions"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateImpersonationSessionById:
    data: InvalidateImpersonationSessionByIdCommand
    command: Literal["InvalidateImpersonationSessionById"] = "InvalidateImpersonationSessionById"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateImpersonationSessionByToken:
    data: InvalidateImpersonationSessionByTokenCommand
    command: Literal["InvalidateImpersonationSessionByToken"] = "InvalidateImpersonationSessionByToken"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateAllImpersonationSessionsForEmployee:
    data: InvalidateAllImpersonationSessionsForEmployeeCommand
    command: Literal["InvalidateAllImpersonationSessionsForEmployee"] = "InvalidateAllImpersonationSessionsForEmployee"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInvalidateAllImpersonationSessionsForUser:
    data: InvalidateAllImpersonationSessionsForUserCommand
    command: Literal["InvalidateAllImpersonationSessionsForUser"] = "InvalidateAllImpersonationSessionsForUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandScimRequest:
    data: ScimRequestCommand
    command: Literal["ScimRequest"] = "ScimRequest"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandLinkScimUser:
    data: LinkScimUserCommand
    command: Literal["LinkScimUser"] = "LinkScimUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCommitScimUserChange:
    data: CommitScimUserChangeCommand
    command: Literal["CommitScimUserChange"] = "CommitScimUserChange"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCreateScimConnection:
    data: CreateScimConnectionCommand
    command: Literal["CreateScimConnection"] = "CreateScimConnection"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchScimConnection:
    data: FetchScimConnectionCommand
    command: Literal["FetchScimConnection"] = "FetchScimConnection"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandPatchScimConnection:
    data: PatchScimConnectionCommand
    command: Literal["PatchScimConnection"] = "PatchScimConnection"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandResetScimApiKey:
    data: ResetScimApiKeyCommand
    command: Literal["ResetScimApiKey"] = "ResetScimApiKey"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandDeleteScimConnection:
    data: DeleteScimConnectionCommand
    command: Literal["DeleteScimConnection"] = "DeleteScimConnection"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandGetScimUsers:
    data: GetScimUsersCommand
    command: Literal["GetScimUsers"] = "GetScimUsers"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandGetScimUser:
    data: GetScimUserCommand
    command: Literal["GetScimUser"] = "GetScimUser"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCreateOidcClient:
    data: CreateOidcClientCommand
    command: Literal["CreateOidcClient"] = "CreateOidcClient"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandFetchOidcClient:
    data: FetchOidcClientCommand
    command: Literal["FetchOidcClient"] = "FetchOidcClient"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandPatchOidcClient:
    data: PatchOidcClientCommand
    command: Literal["PatchOidcClient"] = "PatchOidcClient"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandDeleteOidcClient:
    data: DeleteOidcClientCommand
    command: Literal["DeleteOidcClient"] = "DeleteOidcClient"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandInitiateOidcLogin:
    data: InitiateOidcLoginCommand
    command: Literal["InitiateOidcLogin"] = "InitiateOidcLogin"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data



@dataclass
class CommandCompleteOidcLogin:
    data: CompleteOidcLoginCommand
    command: Literal["CompleteOidcLogin"] = "CompleteOidcLogin"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["data"] = self.data._to_request()
        data["command"] = self.command
        return data




Command = Union[
    CommandPing,
    CommandStartPasskeyRegistration,
    CommandFinishPasskeyRegistration,
    CommandStartPasskeyAuthentication,
    CommandFinishPasskeyAuthentication,
    CommandFetchAllPasskeysForUser,
    CommandDeregisterPasskey,
    CommandDeregisterAllPasskeysForUser,
    CommandCreateDeviceChallenge,
    CommandCreateSession,
    CommandRegisterDevice,
    CommandCreateStatelessToken,
    CommandGetJwks,
    CommandRotateStatelessTokenKey,
    CommandInvalidateSessionByToken,
    CommandInvalidateSessionById,
    CommandInvalidateAllSessionsForUser,
    CommandInvalidateAllSessionsForUserExceptOne,
    CommandFetchAllSessionsForUser,
    CommandFetchAllSessions,
    CommandFetchSessionById,
    CommandUpdateSession,
    CommandUpdateSessions,
    CommandValidateSession,
    CommandValidateAndRefreshSession,
    CommandCreateImpersonationSession,
    CommandValidateImpersonationSession,
    CommandFetchImpersonationSessionById,
    CommandFetchAllImpersonationSessionsForEmployee,
    CommandFetchAllImpersonationSessionsForUser,
    CommandFetchAllActiveImpersonationSessions,
    CommandInvalidateImpersonationSessionById,
    CommandInvalidateImpersonationSessionByToken,
    CommandInvalidateAllImpersonationSessionsForEmployee,
    CommandInvalidateAllImpersonationSessionsForUser,
    CommandScimRequest,
    CommandLinkScimUser,
    CommandCommitScimUserChange,
    CommandCreateScimConnection,
    CommandFetchScimConnection,
    CommandPatchScimConnection,
    CommandResetScimApiKey,
    CommandDeleteScimConnection,
    CommandGetScimUsers,
    CommandGetScimUser,
    CommandCreateOidcClient,
    CommandFetchOidcClient,
    CommandPatchOidcClient,
    CommandDeleteOidcClient,
    CommandInitiateOidcLogin,
    CommandCompleteOidcLogin
]

# Export all types for client imports
__all__ = [
    'Command',
    'CommandPing',
    'CommandStartPasskeyRegistration',
    'CommandFinishPasskeyRegistration',
    'CommandStartPasskeyAuthentication',
    'CommandFinishPasskeyAuthentication',
    'CommandFetchAllPasskeysForUser',
    'CommandDeregisterPasskey',
    'CommandDeregisterAllPasskeysForUser',
    'CommandCreateDeviceChallenge',
    'CommandCreateSession',
    'CommandRegisterDevice',
    'CommandCreateStatelessToken',
    'CommandGetJwks',
    'CommandRotateStatelessTokenKey',
    'CommandInvalidateSessionByToken',
    'CommandInvalidateSessionById',
    'CommandInvalidateAllSessionsForUser',
    'CommandInvalidateAllSessionsForUserExceptOne',
    'CommandFetchAllSessionsForUser',
    'CommandFetchAllSessions',
    'CommandFetchSessionById',
    'CommandUpdateSession',
    'CommandUpdateSessions',
    'CommandValidateSession',
    'CommandValidateAndRefreshSession',
    'CommandCreateImpersonationSession',
    'CommandValidateImpersonationSession',
    'CommandFetchImpersonationSessionById',
    'CommandFetchAllImpersonationSessionsForEmployee',
    'CommandFetchAllImpersonationSessionsForUser',
    'CommandFetchAllActiveImpersonationSessions',
    'CommandInvalidateImpersonationSessionById',
    'CommandInvalidateImpersonationSessionByToken',
    'CommandInvalidateAllImpersonationSessionsForEmployee',
    'CommandInvalidateAllImpersonationSessionsForUser',
    'CommandScimRequest',
    'CommandLinkScimUser',
    'CommandCommitScimUserChange',
    'CommandCreateScimConnection',
    'CommandFetchScimConnection',
    'CommandPatchScimConnection',
    'CommandResetScimApiKey',
    'CommandDeleteScimConnection',
    'CommandGetScimUsers',
    'CommandGetScimUser',
    'CommandCreateOidcClient',
    'CommandFetchOidcClient',
    'CommandPatchOidcClient',
    'CommandDeleteOidcClient',
    'CommandInitiateOidcLogin',
    'CommandCompleteOidcLogin',
]

# Re-export UnexpectedErrorDetails if it was imported
