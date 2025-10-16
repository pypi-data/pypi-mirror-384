"""
Methods for using TileDB hosted arrays, groups, DAGs, and UDFs.

.. deprecated:: 3.0.0
    This module is replaced by `tiledb.client`, which also provides methods for
    using the new TileDB Asset Catalog. Please migrate to importing from
    `tiledb.client`.
"""

import warnings

from ..client import array
from ..client import cloudarray
from ..client import compute
from ..client import dag
from ..client import groups
from ..client import sql
from ..client import udf
from ..client._common import pickle_compat as _pickle_compat
from ..client.array import array_activity
from ..client.array import deregister_array
from ..client.array import info
from ..client.array import register_array
from ..client.client import Config
from ..client.client import Ctx
from ..client.client import login
from ..client.rest_api import models
from ..client.tasks import fetch_results
from ..client.tasks import fetch_results_pandas
from ..client.tasks import fetch_tasks
from ..client.tasks import last_sql_task
from ..client.tasks import last_udf_task
from ..client.tasks import task
from ..client.tiledb_cloud_error import TileDBCloudError

warnings.warn(
    "Please migrate to importing from tiledb.client instead of tiledb.cloud",
    DeprecationWarning,
    stacklevel=2,
)

_pickle_compat.patch_cloudpickle()
_pickle_compat.patch_pandas()

try:
    from tiledb.client.version import version as __version__
except ImportError:
    __version__ = "0.0.0.local"

ResultFormat = models.ResultFormat
UDFResultType = ResultFormat

__all__ = (
    "array",
    "cloudarray",
    "compute",
    "dag",
    "files",
    "folders",
    "groups",
    "list_assets",
    "sql",
    "tokens",
    "udf",
    "array_activity",
    "deregister_array",
    "info",
    "register_array",
    "Config",
    "Ctx",
    "login",
    "organization",
    "organizations",
    "user_profile",
    "last_sql_task",
    "last_udf_task",
    "task",
    "fetch_tasks",
    "fetch_results",
    "fetch_results_pandas",
    "TileDBCloudError",
    "workspaces",
)
