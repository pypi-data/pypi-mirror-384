"""TileDB Teamspaces

A teamspace is a container for assets and folders of assets. It will be
backed by a unique cloud storage location and may be mounted as a
directory in Notebooks and UDFs.

The TileDB web UI is the primary tool for managing teamspaces, but some
functionality is available via this module.
"""

from typing import List, Optional, Union

import tiledb.client
from tiledb.client import client
from tiledb.client._common.api_v4.api import TeamspacesApi
from tiledb.client._common.api_v4.exceptions import ApiException
from tiledb.client._common.api_v4.models import Teamspace
from tiledb.client._common.api_v4.models import TeamspacesCreateRequest
from tiledb.client._common.api_v4.models import TeamspaceVisibility

# Re-export the models for convenience.
__all__ = [
    "Teamspace",
    "TeamspacesCreateRequest",
    "TeamspaceVisibility",
    "TeamspacesError",
    "create_teamspace",
    "list_teamspaces",
]


class TeamspacesError(tiledb.TileDBError):
    """Raised when a teamspaces CRUD operation fails."""


def create_teamspace(
    name: str,
    *,
    description: str = "New teamspace",
    visibility: TeamspaceVisibility = TeamspaceVisibility.PRIVATE,
) -> Teamspace:
    """Create a new teamspace in the current workspace.

    Parameters
    ----------
    name : str
        The name of the teamspace to create.
    description : str, optional
        Description of the teamspace to create.
    visibility : TeamspaceVisibility, optional
        Private is the default, but teamspaces may be public.

    Returns
    -------
    Teamspace

    Raises
    ------
    TeamspacesError:
        If the teamspace creation request failed.

    Examples
    --------
    >>> teamspace1 = teamspaces.create_teamspace(
    ...     "teamspace1",
    ...     description="Teamspace One",
    ...     visibility="private",
    ... )

    """
    create_teamspace_request = TeamspacesCreateRequest(
        name=name, description=description, visibility=visibility
    )
    try:
        create_teamspace_response = client.client.build(
            TeamspacesApi
        ).create_teamspaces(client.get_workspace_id(), create_teamspace_request)
    except ApiException as exc:
        raise TeamspacesError("The teamspace creation request failed.") from exc
    else:
        return create_teamspace_response.data


def delete_teamspace(
    teamspace: Union[Teamspace, str],
) -> None:
    """Create a new teamspace in the current workspace.

    Parameters
    ----------
    teamspace : Teamspace or str
        The teamspace to which the uploaded file will belong.

    Raises
    ------
    TeamspacesError:
        If the teamspace deletion request failed.

    Examples
    --------
    >>> teamspaces.delete_teamspace("teamspace1")

    """
    try:
        client.client.build(TeamspacesApi).delete_teamspace(
            client.get_workspace_id(), getattr(teamspace, "teamspace_id", teamspace)
        )
    except ApiException as exc:
        raise TeamspacesError("The teamspace deletion request failed.") from exc


def list_teamspaces(
    *,
    memberships: Optional[bool] = None,
    order_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[Teamspace]:
    """List teamspaces of the current workspace.

    This function can filter teamspaces based on the user's membership
    and control the sorting of the results.

    Parameters
    ----------
    memberships : bool, optional
        If True, returns teamspaces the user is a member of.
        If False, returns public teamspaces in the workspace that the
        user is NOT a member of.
        If not provided (default), the API's default behavior is used, which
        is typically to return all teamspaces the user has access to.
    order_by : str, optional
        The field to order the results by. Defaults to 'created_at'.
        Valid values include 'name', 'created_at', 'updated_at'.
    order : str, optional
        The sorting direction. Defaults to 'desc'.
        Valid values are 'asc', 'desc'.

    Returns
    -------
    list[Teamspace]
        A list of Teamspace objects.

    Raises
    ------
    TeamspacesError
        If the teamspaces listing request failed.

    Examples
    --------
    # List all teamspaces you are a member of
    >>> my_teamspaces = teamspaces.list_teamspaces(memberships=True)
    >>> [ts.name for ts in my_teamspaces]
    ["my-first-teamspace"]

    # List public teamspaces you are NOT a member of, ordered by name
    >>> public_teamspaces = teamspaces.list_teamspaces(
    ...     memberships=False, order_by="name", order="asc"
    ... )

    """
    try:
        resp = client.client.build(TeamspacesApi).list_teamspaces(
            client.get_workspace_id(),
            memberships=memberships,
            order_by=order_by,
            order=order,
        )
    except ApiException as exc:
        raise TeamspacesError("The teamspaces listing request failed.") from exc
    else:
        return resp.data
