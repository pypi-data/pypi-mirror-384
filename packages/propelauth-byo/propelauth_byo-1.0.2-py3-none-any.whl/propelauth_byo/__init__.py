"""PropelAuth Python Client Library"""

# Main client and factory function
from .propel_auth_client import PropelAuthClient, create_client

# Sub-clients
from .passkey_client import PasskeyClient
from .session_client import SessionClient
from .device_client import DeviceClient
from .scim_client import ScimClient
from .scim_management_client import ScimManagementClient
from .impersonation_client import ImpersonationClient
from .sso_client import SsoClient
from .sso_management_client import SsoManagementClient

# Result type for error handling
from .result import Result, Ok, Err, is_ok, is_err

__all__ = [
    # Main client
    "PropelAuthClient",
    "create_client",
    # Sub-clients
    "PasskeyClient",
    "SessionClient",
    "DeviceClient",
    "ScimClient",
    "ScimManagementClient",
    "ImpersonationClient",
    "SsoClient",
    "SsoManagementClient",
    # Result types
    "Result",
    "Ok",
    "Err",
    "is_ok",
    "is_err",
]

__version__ = "1.0.2"
