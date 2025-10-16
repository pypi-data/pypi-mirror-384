import json
from typing import Any, Dict, Optional, Tuple

import urllib3

from tiledb.client import client
from tiledb.client import rest_api
from tiledb.client._common import json_safe
from tiledb.client._common import utils
from tiledb.client.taskgraphs import builder


def register(
    graph: builder.TaskGraphBuilder,
    name: Optional[str] = None,
    *,
    workspace: Optional[str] = None,
) -> None:
    """Registers the graph constructed by the TaskGraphBuilder.

    :param graph: The graph to register.
    :param name: The name to register the graph with. By default, will use the
        ``name`` specified in ``graph``. This must be a bare name, with no
        workspace (i.e. ``my-graph``, not ``me/my-graph``).
    :param workspace: The workspace, if not your own, to register the graph in.
    """
    api_client = client.build(rest_api.RegisteredTaskGraphsApi)
    name = name or graph.name

    api_client.register_registered_task_graph(
        workspace=workspace,
        name=name,
        graph=json_safe.Value(graph._tdb_to_json(override_name=name)),
    )


def load(
    name_or_nsname: str,
    *,
    workspace: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves the given task graph from the server.

    :param name_or_nsname: The graph's identifier, either in the form
        ``workspace/name``, or just ``name`` to use the ``workspace`` param.
    :param workspace: If set, the workspace of the graph.
        If ``name_or_nsname`` is of the form ``workspace/name``, must be None.
        If ``name_or_nsname`` is just a name and this is None, will use the
        current user's workspace.
    """
    name, workspace = _canonicalize(name_or_nsname, workspace)
    api_client = client.build(rest_api.RegisteredTaskGraphsApi)

    result: urllib3.HTTPResponse = api_client.get_registered_task_graph(
        workspace=workspace,
        name=name,
        _preload_content=False,
    )
    try:
        return json.loads(result.data)
    finally:
        utils.release_connection(result)


def update(
    graph: builder.TaskGraphBuilder,
    old_name: Optional[str] = None,
    *,
    workspace: Optional[str] = None,
) -> None:
    """Updates the registered task graph at the given location.

    :param graph: The new graph to replace the old value.
    :param old_name: The name of the graph to rename from, if present.
        If ``graph`` is to be renamed, the new name of the graph must appear
        in ``graph.name``.
    :param workspace: The workspace, if not your own, where the graph will
        be updated.
    """
    api_client = client.build(rest_api.RegisteredTaskGraphsApi)
    name = old_name or graph.name
    api_client.update_registered_task_graph(
        name=name,
        workspace=workspace,
        graph=json_safe.Value(graph._tdb_to_json()),
    )


def delete(name: str) -> None:
    """Deletes the given task graph.

    This deregisters the graph and also removes the graph array from storage.

    :param name: The graph's identifier.
    """
    api_client = client.build(rest_api.RegisteredTaskGraphsApi)
    api_client.delete_registered_task_graph(client.get_workspace_id(), name)


def _canonicalize(
    name_or_nsname: str,
    workspace: Optional[str],
) -> Tuple[str, str]:
    """Canonicalizes the inputs into the actual (name, workspace) pair."""
    if "/" in name_or_nsname:
        if workspace:
            raise ValueError(
                "If `workspace` is set, `name_or_nsname` cannot be of the form"
                " workspace/name"
            )
        workspace, _, name = name_or_nsname.partition("/")
        return name, workspace
    return (
        name_or_nsname,
        workspace or client.default_user().username,
    )
