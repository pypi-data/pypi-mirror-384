"""TileDB workspaces."""

import tiledb

from . import client
from ._common.api_v4 import Workspace
from ._common.api_v4 import WorkspacesApi
from .rest_api import ApiException


class WorkspacesError(tiledb.TileDBError):
    """Raised when workspaces can not be accessed."""


def get_workspace(name_or_id: str) -> Workspace:
    """Get the representation of a workspace by its name or id.

    Parameters
    ---------
    name_or_id : str
        The name or id of the workspace.

    Returns
    -------
    Workspace

    Raises
    ------
    WorkspacesError
        If the retrieval request fails.

    """
    try:
        workspaces_api = client.client.build(WorkspacesApi)
        resp = workspaces_api.get_workspace(name_or_id)
    except ApiException as exc:
        raise WorkspacesError("The workspace retrieval request failed.") from exc
    else:
        return resp.data
