"""TileDB client and supporting methods, such as login()

Examples
--------
Login and configure a client session from a named profile.

>>> tiledb.client.login(profile_name=PROFILE_NAME)

"""

import enum
import logging
import os
import threading
import types
import uuid
from concurrent import futures
from typing import Callable, Optional, Sequence, TypeVar, Union

import urllib3

import tiledb
import tiledb.client._common.api_v2.models as models_v2
import tiledb.client._common.api_v4.models as models_v4
import tiledb.client.rest_api.models as models_v1
from tiledb.client import config
from tiledb.client import rest_api
from tiledb.client._common.api_v4 import ApiClient
from tiledb.client._common.api_v4 import APIToken
from tiledb.client._common.api_v4 import TokenCreateRequest
from tiledb.client._common.api_v4 import TokensApi
from tiledb.client._common.api_v4 import TokenScope
from tiledb.client._common.api_v4 import User
from tiledb.client._common.api_v4 import UsersApi
from tiledb.client._common.api_v4 import UserSelfWorkspace
from tiledb.client._common.api_v4 import WorkspacesApi
from tiledb.client.pool_manager_wrapper import _PoolManagerWrapper

_T = TypeVar("_T")

logger = logging.getLogger(__name__)


def Config(cfg_dict=None):
    """
    Builds a tiledb config setting the login parameters that exist for the cloud service
    :return: tiledb.Config
    """
    restricted = ("rest.server_address", "rest.username", "rest.password")

    if not cfg_dict:
        cfg_dict = dict()

    for r in restricted:
        if r in cfg_dict:
            raise ValueError(f"Unexpected config parameter '{r}' to cloud.Config")

    host = config.config.host

    cfg_dict["rest.server_address"] = host
    cfg = tiledb.Config(cfg_dict)

    if (
        config.config.username is not None
        and config.config.username != ""
        and config.config.password is not None
        and config.config.password != ""
    ):
        cfg["rest.username"] = config.config.username
        cfg["rest.password"] = config.config.password
    else:
        cfg["rest.token"] = config.config.api_key["X-TILEDB-REST-API-KEY"]

    return cfg


def Ctx(config=None):
    """
    Builds a TileDB Context that has the tiledb config parameters
    for tiledb cloud set from stored login
    :return: tiledb.Ctx
    """
    return tiledb.Ctx(Config(config))


class LoginError(tiledb.TileDBError):
    """Raise for errors during login"""


class ConfigurationError(tiledb.TileDBError):
    """Raise for errors during configuration"""


def configure(
    token: Optional[Union[APIToken, str]] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    workspace: Optional[str] = None,
    host: Optional[str] = None,
    verify_ssl: Optional[bool] = None,
    profile_name: Optional[str] = None,
    profile_dir: Optional[str] = None,
) -> None:
    """
    Store TileDB credentials in a profile for later use.

    This method handles credential storage and profile management, allowing
    you to save authentication details to disk for use in subsequent sessions.
    After configuring credentials, you can use login() to load and activate
    them for the current session.

    Note
    ----
    If both token and username/password are provided, only the token will be
    stored in the profile. The username and password parameters will be ignored
    when a token is present, as token-based authentication takes priority.

    Parameters
    ----------
    token: str, optional
        API token for authentication. This token may be one that identifies
        a workspace.
    username: str, optional
        A TileDB account username.
    password: str, optional
        A TileDB account password.
    workspace: str, optional
        A TileDB workspace name or id.
    host: str, optional
        The TileDB server address.
    verify_ssl: bool, optional
        Enable strict SSL verification.
    profile_name: str, optional
        The name to assign to the profile. Defaults to "default".
    profile_dir: str, optional
        The directory where the profiles file is stored. Defaults to
        None, which means the home directory of the user.

    Raises
    ------
    ConfigurationError
        If the configuration fails due to missing or invalid parameters.

    Examples
    Configure credentials using username and password:

    >>> tiledb.client.configure(
    ...     username="myuser",
    ...     password="mypass",
    ...     workspace="myworkspace",
    ...     host="myhost.com"
    ... )

    Configure credentials using an API token:

    >>> tiledb.client.configure(
    ...     token="my-api-token",
    ...     workspace="myworkspace",
    ...     host="myhost.com"
    ... )

    Configure credentials to a named profile:

    >>> tiledb.client.configure(
    ...     token="my-token",
    ...     workspace="myworkspace",
    ...     host="myhost.com",
    ...     profile_name="production"
    ... )

    """

    # Prepare profile for saving
    profile = tiledb.Profile(profile_name, profile_dir)

    # Validate and set host
    if not host:
        raise ConfigurationError("Host is required.")

    host = host.rstrip("/")
    if not host.startswith(("http://", "https://")):
        host = f"https://{host}"
    profile["rest.server_address"] = host

    # Handle token-based authentication
    if token:
        if isinstance(token, str):
            # Attempt to parse workspace from the token if not provided
            if not workspace:
                try:
                    _, middle, _ = token.split("-")
                    if middle.startswith("ws_"):
                        workspace = middle
                except ValueError:
                    pass

            profile["rest.token"] = token
        else:
            # APIToken object
            workspace = workspace or getattr(token, "workspace_id", None)
            api_key = getattr(token, "api_key", token)
            profile["rest.token"] = api_key

    # Handle username/password authentication (only if no token provided)
    else:
        if username:
            profile["rest.username"] = username
        if password:
            profile["rest.password"] = password

    # Validate that we have either token or username/password
    if not (token or (username and password)):
        raise ConfigurationError(
            "Either token OR both username and password must be provided."
        )

    # Validate username/password are both present if one is provided (only when not using token)
    if not token and ((username and not password) or (password and not username)):
        raise ConfigurationError(
            "Both username and password are required when using username/password authentication."
        )

    # Validate workspace requirements
    if not workspace:
        raise ConfigurationError(
            "Workspace is required. Provide workspace or use a token with a workspace id in format ws_*."
        )

    # Set common profile values
    profile["rest.workspace"] = workspace

    if verify_ssl is False:
        profile["rest.verify_ssl"] = "false"

    # Remove existing profile and save new one
    try:
        tiledb.Profile.remove(profile_name, profile_dir)
    except tiledb.TileDBError:
        pass

    profile.save()


def login(
    profile_name: Optional[str] = None,
    profile_dir: Optional[str] = None,
    no_session: Optional[bool] = False,
    threads: Optional[int] = None,
) -> None:
    """
    Login and configure a TileDB client session using stored credentials.

    This method loads credentials from a TileDB profile that was previously
    saved using configure(). It does not store or modify credentials; it only
    loads them from disk to establish a session.

    To store credentials for the first time, use configure() first, then
    call login() to activate them.

    You may call this function multiple times within a Python interpreter
    session to switch between TileDB profiles and configure new client
    sessions.

    Parameters
    ----------
    profile_name: str, optional
        Name of the configuration profile to use. If not specified, the
        default profile will be used if it exists.
    profile_dir: str, optional
        The directory where the profiles file is stored. Defaults to
        None, which means the home directory of the user.
    no_session: bool, optional
        Don't create a session token on login, store
        instead username/password, defaults to False.
    threads: int, optional
        Number of threads to enable for concurrent requests, default to
        None (determined by library).

    Raises
    ------
    LoginError
        If the login fails due to missing configuration parameters or
        if no valid profile can be found.

    Examples
    --------
    Login using the default profile:

    >>> tiledb.client.login()

    Login using a named profile:

    >>> tiledb.client.login(profile_name="production")

    """
    global build
    global client

    # Remember original environment variable values for cleanup
    original_profile_name = os.environ.get("TILEDB_PROFILE_NAME")
    original_profile_dir = os.environ.get("TILEDB_PROFILE_DIR")

    try:
        # Set or clear environment variables for load_configuration to pick up
        # This is also required for the rest of the tiledb packages to
        # be aware of the profile in use.
        # If user doesn't specify profile_name, clear it to use default
        if profile_name:
            os.environ["TILEDB_PROFILE_NAME"] = profile_name
        else:
            os.environ.pop("TILEDB_PROFILE_NAME", None)

        # If user doesn't specify profile_dir, clear it to use default
        if profile_dir:
            os.environ["TILEDB_PROFILE_DIR"] = profile_dir
        else:
            os.environ.pop("TILEDB_PROFILE_DIR", None)

        # Clear any existing configuration to force reload
        config._config = None
        config._workspace_id = None

        # Use load_configuration to load profile data into config
        config.load_configuration()

        # Get values from the loaded config object
        username = config.config.username
        password = config.config.password
        host = config.config.host
        workspace = config._workspace_id
        verify_ssl = config.config.verify_ssl

        # Check if we have a token available
        token = None
        if config.config.api_key and "X-TILEDB-REST-API-KEY" in config.config.api_key:
            token = config.config.api_key["X-TILEDB-REST-API-KEY"]

    except (tiledb.TileDBError, config.ConfigurationError, KeyError) as exc:
        # Restore original environment variables on error
        if original_profile_name is not None:
            os.environ["TILEDB_PROFILE_NAME"] = original_profile_name
        else:
            os.environ.pop("TILEDB_PROFILE_NAME", None)

        if original_profile_dir is not None:
            os.environ["TILEDB_PROFILE_DIR"] = original_profile_dir
        else:
            os.environ.pop("TILEDB_PROFILE_DIR", None)

        raise LoginError(
            f"Failed to load configuration profile {profile_name}. "
            "Use configure() to store credentials first."
        ) from exc

    # If no token is available but we have username/password, create a session token
    # (token takes priority over username/password)
    if not token and username and password and not no_session:

        client.set_threads(threads)

        # Create a session type token with maximum scope.
        with ApiClient(config.config) as api_client:
            # Get workspace id from name.
            workspaces_api = WorkspacesApi(api_client)
            resp = workspaces_api.get_workspace(workspace)
            workspace = resp.data.workspace_id

            request = TokenCreateRequest(
                name=f"login-session-{uuid.uuid4()}",
                scope=TokenScope._,
                workspace_id=workspace,
            )
            tokens_api = TokensApi(api_client)

            logger.debug(
                "Creating token: request=%r, host=%r, workspace_id=%r",
                request,
                config.config.host,
                workspace,
            )

            resp = tokens_api.create_token(request)
            session_token = resp.data

            logger.debug("Created token: resp=%r, token=%r", resp, session_token)

        # Handle the new session token
        if session_token:
            if isinstance(session_token, str):
                # Attempt to parse workspace from the token.
                try:
                    _, middle, _ = session_token.split("-")
                    if middle.startswith("ws_"):
                        workspace = middle
                except ValueError:
                    logger.info(
                        "No workspace id detected in token. Workspace's format must be ws_*."
                    )

            workspace = workspace or getattr(session_token, "workspace_id", None)
            if not workspace:
                raise LoginError("Unknown workspace.")

            api_key = getattr(session_token, "api_key", session_token)

            # Reconfigure with token-based auth
            config.setup_configuration(
                api_key={"X-TILEDB-REST-API-KEY": api_key},
                username=None,
                password=None,
                host=host,
                verify_ssl=verify_ssl,
                workspace=workspace,
            )

    # Set the workspace id
    config._workspace_id = workspace

    # Re-initialize the global session client and API builder.
    client = Client()
    build = client.build


def get_workspace_id() -> str:
    """Get the current session's workspace id."""
    # Trigger profile configuration loading.
    _ = config.config

    if not config._workspace_id:
        raise ConfigurationError("Workspace is undefined.")

    if not config._workspace_id.startswith("ws_"):
        with ApiClient(config.config) as api_client:
            workspaces_api = WorkspacesApi(api_client)
            resp = workspaces_api.get_workspace(config._workspace_id)
            config._workspace_id = resp.data.workspace_id

    return config._workspace_id


def get_self_user() -> tuple[User, UserSelfWorkspace]:
    """Get the currently logged-in user and related workspaces.

    Returns
    -------
    tuple[User, UserSelfWorkspace]
    """
    api_instance = build(UsersApi)
    get_self_user_response = api_instance.get_self_user()
    return (get_self_user_response.data.user, get_self_user_response.data.workspaces)


def default_user() -> User:
    """Get the currently logged-in user..

    Returns
    -------
    User
    """
    user, _ = get_self_user()
    return user


class RetryMode(enum.Enum):
    DEFAULT = "default"
    FORCEFUL = "forceful"
    DISABLED = "disabled"

    def maybe_from(v: "RetryOrStr") -> "RetryMode":
        if isinstance(v, RetryMode):
            return v
        return RetryMode(v)


RetryOrStr = Union[RetryMode, str]


_RETRY_CONFIGS = {
    RetryMode.DEFAULT: urllib3.Retry(
        total=100,
        backoff_factor=0.25,
        status_forcelist=[503],
        allowed_methods=[
            "HEAD",
            "GET",
            "PUT",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "POST",
            "PATCH",
        ],
        raise_on_status=False,
        # Don't remove any headers on redirect
        remove_headers_on_redirect=[],
    ),
    RetryMode.FORCEFUL: urllib3.Retry(
        total=100,
        backoff_factor=0.25,
        status_forcelist=[400, 500, 501, 502, 503],
        allowed_methods=[
            "HEAD",
            "GET",
            "PUT",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "POST",
            "PATCH",
        ],
        raise_on_status=False,
        # Don't remove any headers on redirect
        remove_headers_on_redirect=[],
    ),
    RetryMode.DISABLED: False,
}


class Client:
    """
    TileDB Client.

    :param pool_threads: Number of threads to use for http requests
    :param retry_mode: Retry mode ["default", "forceful", "disabled"]
    """

    def __init__(
        self,
        pool_threads: Optional[int] = None,
        retry_mode: RetryOrStr = RetryMode.DEFAULT,
    ):
        """

        :param pool_threads: Number of threads to use for http requests
        :param retry_mode: Retry mode ["default", "forceful", "disabled"]
        """
        self._pool_lock = threading.Lock()
        self._set_threads(pool_threads)
        # Low-level clients begin uninitialized.
        # They are initialized just before they are needed.
        self._mode = retry_mode
        self.__client_v1 = None
        self.__client_v2 = None
        self.__client_v4 = None

    @property
    def _client_v1(self):
        if not self.__client_v1:
            self._retry_mode(self._mode)
            self._rebuild_clients()
        return self.__client_v1

    @property
    def _client_v2(self):
        if not self.__client_v2:
            self._retry_mode(self._mode)
            self._rebuild_clients()
        return self.__client_v2

    @property
    def _client_v4(self):
        if not self.__client_v4:
            self._retry_mode(self._mode)
            self._rebuild_clients()
        return self.__client_v4

    def build(self, builder: Callable[[rest_api.ApiClient], _T]) -> _T:
        """Builds an API client with the given config."""
        if builder.__module__.startswith("tiledb.client._common.api_v4"):
            return builder(self._client_v4)
        elif builder.__module__.startswith("tiledb.client._common.api_v2"):
            return builder(self._client_v2)
        return builder(self._client_v1)

    def set_disable_retries(self):
        self.retry_mode(RetryMode.DISABLED)

    def set_default_retries(self):
        self.retry_mode(RetryMode.DEFAULT)

    def set_forceful_retries(self):
        self.retry_mode(RetryMode.FORCEFUL)

    def retry_mode(self, mode: RetryOrStr = RetryMode.DEFAULT) -> None:
        """Sets how we should retry requests and updates API instances."""
        self._retry_mode(mode)
        self._rebuild_clients()

    def set_threads(self, threads: Optional[int] = None) -> None:
        """Updates the number of threads in the async thread pool."""
        self._set_threads(threads)
        self._rebuild_clients()

    def _retry_mode(self, mode: RetryOrStr) -> None:
        mode = RetryMode.maybe_from(mode)
        config.config.retries = _RETRY_CONFIGS[mode]
        self._mode = mode

    def _rebuild_clients(self) -> None:
        self.__client_v1 = self._rebuild_client(models_v1)
        self.__client_v2 = self._rebuild_client(models_v2)
        self.__client_v4 = self._rebuild_client(models_v4)

    def _rebuild_client(self, module: types.ModuleType) -> rest_api.ApiClient:
        """
        Initialize api clients
        """
        # If users increase the size of the thread pool, increase the size
        # of the connection pool to match. (The internal members of
        # ThreadPoolExecutor are not exposed in the .pyi files, so we silence
        # mypy's warning here.)
        pool_size = self._thread_pool._max_workers  # type: ignore[attr-defined]
        config.config.connection_pool_maxsize = pool_size
        client = rest_api.ApiClient(config.config, _tdb_models_module=module)
        client.rest_client.pool_manager = _PoolManagerWrapper(
            client.rest_client.pool_manager
        )
        return client

    def _set_threads(self, threads) -> None:
        with self._pool_lock:
            old_pool = getattr(self, "_thread_pool", None)
            self._thread_pool = futures.ThreadPoolExecutor(
                threads, thread_name_prefix="tiledb-async-"
            )
        if old_pool:
            old_pool.shutdown(wait=False)

    def _pool_submit(
        self,
        func: Callable[..., _T],
        *args,
        **kwargs,
    ) -> "futures.Future[_T]":
        with self._pool_lock:
            return self._thread_pool.submit(func, *args, **kwargs)


client = Client()
build = client.build


def _maybe_unwrap(param: Union[None, str, Sequence[str]]) -> Optional[str]:
    """Unwraps the first value if passed a sequence of strings."""
    if param is None or isinstance(param, str):
        return param
    try:
        return param[0]
    except IndexError:
        # If we're passed an empty sequence, treat it as no parameter.
        return None


def _uuid_to_str(param: Union[None, str, uuid.UUID]) -> Optional[str]:
    if isinstance(param, uuid.UUID):
        return str(param)
    return param


def _maybe_wrap(param: Union[None, str, Sequence[str]]) -> Optional[Sequence[str]]:
    """Wraps the value in a sequence if passed an individual string."""
    if isinstance(param, str):
        return (param,)
    return param
