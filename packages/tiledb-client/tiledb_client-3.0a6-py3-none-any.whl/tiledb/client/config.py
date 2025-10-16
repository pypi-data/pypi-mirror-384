"""TileDB client session configuration

This module maintains the global state of client session configuration
and several methods for loading it from and saving it to profiles on
disk.

"""

# "config" is a dynamic attribute of this module. The actual state of
# the attribute is bound to "_config", which begins uninitialized.
# Looking up "config" from tiledb.client.config causes our stored
# configuration to be loaded just as needed, and makes calling login()
# unnecessary in many cases.

import logging

from urllib3 import Retry

import tiledb
from tiledb.client._common.api_v4 import configuration

logger = logging.getLogger(__name__)


class ConfigurationError(tiledb.TileDBError):
    """Raise for configuration-related errors"""


_config = None
_workspace_id = None


def __getattr__(name):
    if name == "config":
        if _config is None:
            load_configuration()
        return _config
    else:
        raise AttributeError


def load_configuration() -> None:
    """Loads parameters and configures the session's client.

    Configuration parameters are obtained from the user's default TileDB
    profile or from the environment via tiledb.Config.

    This enables login-free execution of Python applications using the
    default profile and/or properly configured environment. To use
    a different profile, one must call tiledb.client.login().

    Configuration parameters may come from several sources, in order of
    precedence:

    - user-configured config values
    - environment variables
    - profile values
    - default config values

    Raises
    ------
    ConfigurationError
        When configuration parameters are not sufficent and server
        requests are not possible.

    Notes
    -----
    This function is called once at most during any Python interpreter
    session or program lifetime, on the first access of
    tiledb.client.config, such as during the first HTTP server request.

    """
    config_py = tiledb.Config()
    token = config_py.get("rest.token", False)
    username = config_py.get("rest.username", False)
    password = config_py.get("rest.password", False)
    host = config_py.get("rest.server_address", False)
    verify_ssl = config_py.get("rest.verify_ssl", False)
    workspace = config_py.get("rest.workspace", False)

    if not token and not (username and password):
        raise ConfigurationError(
            "Authentication parameters were not found in the environment or default profile. Call tiledb.client.login() to continue."
        )

    if token:
        api_key = {"X-TILEDB-REST-API-KEY": token}
        # Attempt to parse workspace from the token.
        try:
            _, middle, _ = token.split("-")
            if middle.startswith("ws_"):
                workspace = middle
        except ValueError:
            logger.info("No workspace id detected in token.")
    else:
        api_key = {}

    if not workspace:
        raise ConfigurationError(
            "The workspace was not found in the environment or default profile. Call tiledb.client.login() to continue."
        )

    if not host:
        raise ConfigurationError(
            "The server host was not found in the environment or default profile. Call tiledb.client.login() to continue."
        )

    setup_configuration(
        api_key=api_key,
        username=username,
        password=password,
        host=host,
        verify_ssl=verify_ssl,
        workspace=workspace,
    )


def setup_configuration(
    api_key=None,
    host="",
    username=None,
    password=None,
    verify_ssl=True,
    workspace=None,
) -> None:
    """Configures the session's client."""
    global _config
    global _workspace_id

    # Re-initialize the global session configuration.
    cfg_kwds = {
        "api_key": api_key or {},
        "host": host,
    }
    if username and password:
        cfg_kwds.update(username=username, password=password)

    _config = configuration.Configuration(**cfg_kwds)

    if verify_ssl is False:
        _config.verify_ssl = verify_ssl

    _config.retries = Retry(
        total=10,
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
        remove_headers_on_redirect=[],
    )

    _workspace_id = workspace


# Loading of the default configuration file and determination of
# whether we are logged in or not is now deferred to the first access
# of this module's "config" attribute.
_workspace_id = None
