"""Auto-generated from TypeScript type: ScimUserMatchingStrategy"""
from typing import Literal

ScimUserMatchingStrategy = Literal[
    "OidcSubToScimUsername",
    "OidcSubToScimExternalId",
    "OidcEmailToScimUsername",
    "OidcEmailUsernameToScimUsername",
    "OidcPreferredUsernameToScimUsername"
]