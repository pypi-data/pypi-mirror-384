"""Access to API tokens."""

import datetime

import tiledb

from . import client
from ._common.api_v4 import TokenCreateRequest
from ._common.api_v4 import TokensApi
from ._common.api_v4 import TokenScope
from .rest_api import ApiException


class TokensError(tiledb.TileDBError):
    """Raised when tokens cannot be created or revoked."""


def create_token(name: str, scope: TokenScope, expires_at: datetime):
    """Create and retrieve an API token.

    Allowed scope values are:

    _ = "*"
    PASSWORD_RESET = "password_reset"
    CONFIRM_EMAIL = "confirm_email"
    USER_READ = "user:read"
    USER_READ_WRITE = "user:read-write"
    USER_ADMIN = "user:admin"
    ARRAY_READ = "array:read"
    ARRAY_READ_WRITE = "array:read-write"
    ARRAY_ADMIN = "array:admin"
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_READ_WRITE = "organization:read-write"
    ORGANIZATION_ADMIN = "organization:admin"
    GROUP_READ = "group:read"
    GROUP_READ_WRITE = "group:read-write"
    GROUP_ADMIN = "group:admin"

    Parameters
    ---------
    name : str
        The name of the token. Will be modified by the server to enforce uniqueness.
    scope : TokenScope
        See the enumeration of allowed values above.
    expires_at: datetime
        The expiration date of the token.

    Returns
    -------
    Token

    Raises
    ------
    TokensError
        If the token creation request fails.

    """
    try:
        req = TokenCreateRequest(
            name=name,
            scope=scope,
            expires_at=expires_at,
            workspace_id=client.get_workspace_id(),
        )
        tokens_api = client.client.build(TokensApi)
        resp = tokens_api.create_token(req)
        token = resp.data
    except ApiException as exc:
        raise TokensError("The token creation request failed.") from exc
    else:
        return token
