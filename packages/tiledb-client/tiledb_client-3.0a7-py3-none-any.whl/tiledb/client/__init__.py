"""
Methods for using TileDB teamspaces, assets, DAGs, and UDFs.

Examples
--------
Before using TileDB you must authenticate by configuring a profile and then
using it to log in. Please note that in the examples below the names of
workspaces, teamspaces, and assets are only example names.

First configure your credentials (this saves them to a profile):

>>> import tiledb.client
>>> tiledb.client.configure(token="TOKEN", workspace="WORKSPACE")

Then login using the stored credentials:

>>> tiledb.client.login()

To store credentials in a named profile:

>>> tiledb.client.configure(token="TOKEN", workspace="WORKSPACE", profile_name="PROFILE")

To use a named profile:

>>> tiledb.client.login(profile_name="PROFILE")

Once you have a **default** profile configured, you may use TileDB without
explicitly calling login(). The profile will be loaded automatically.
In TileDB notebooks and user-defined functions, no configuration or
login step is required. These sessions are already authenticated.

The name of the workspace for your current session is accessible from
the client context configuration and also from a method of this module.

>>> tiledb.client.Ctx().config()["rest.workspace"]
"WORKSPACE"
>>> tiledb.client.get_workspace_id()
"WORKSPACE"

The list of teamspaces you can access is provided by the `teamspaces`
module.

>>> from tiledb.client import teamspaces
>>> [item.name for item in teamspaces.list_teamspaces()]
["general"]

The list of assets in in a teamspace is provided by the `assets` module.

>>> from tiledb.client import assets
>>> [item.name for item in assets.list_assets(teamspace="general")]
["README.md"]

"""

from . import array
from . import assets
from . import compute
from . import dag
from . import files
from . import folders
from . import groups
from . import sql
from . import teamspaces
from . import tokens
from . import udf
from . import workspaces
from ._common import pickle_compat as _pickle_compat
from .client import Config
from .client import ConfigurationError
from .client import Ctx
from .client import configure
from .client import get_workspace_id
from .client import login

_pickle_compat.patch_cloudpickle()
_pickle_compat.patch_pandas()

try:
    from tiledb.client.version import version as __version__
except ImportError:
    __version__ = "0.0.0.local"

__all__ = (
    "Config",
    "configure",
    "ConfigurationError",
    "Ctx",
    "array",
    "asset",
    "assets",
    "compute",
    "dag",
    "files",
    "folders",
    "get_workspace_id",
    "groups",
    "login",
    "sql",
    "teamspaces",
    "tokens",
    "udf",
    "workspaces",
)
