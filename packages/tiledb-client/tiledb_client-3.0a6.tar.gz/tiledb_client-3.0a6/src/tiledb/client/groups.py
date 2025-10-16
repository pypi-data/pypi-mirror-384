"""Functions for managing TileDB Cloud groups."""

import inspect
import posixpath
import urllib.parse
from typing import List, Optional

from . import client
from . import rest_api
from . import tiledb_cloud_error
from ._common import api_v2
from ._common import utils
from .rest_api.models import group_update

split_uri = utils.split_uri


def create(
    name: str,
    *,
    namespace: Optional[str] = None,
    parent_uri: Optional[str] = None,
    storage_uri: Optional[str] = None,
    credentials_name: Optional[str] = None,
) -> None:
    """Creates a new TileDB Cloud group.

    :param name: The name of the group to create, or its URI.
    :param namespace: The namespace to create the group in.
        If ``name`` is a URI, this must not be provided.
        If not provided, the current logged-in user will be used.
    :param parent_uri: The parent URI to add the group to, if desired.
    :param storage_uri: The backend URI where the group will be stored.
        If not provided, uses the namespace's default storage path for groups.
    :param credentials_name: The name of the storage credential to use for
        creating the group. If not provided, uses the namespace's default
        credential for groups.
    """
    namespace, name = utils.canonicalize_nameuri_namespace(name, namespace)

    groups_client = client.build(api_v2.GroupsApi)
    groups_client.create_group(
        group_namespace=namespace,
        x_tiledb_cloud_access_credentials_name=credentials_name,
        group_creation=api_v2.GroupCreationRequest(
            group_details=api_v2.GroupCreationRequestGroupDetails(
                name=name,
                uri=storage_uri,
            )
        ),
    )
    if parent_uri:
        _add_to(namespace=namespace, name=name, parent_uri=parent_uri)


def register(
    storage_uri: str,
    *,
    dest_uri: Optional[str] = None,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    credentials_name: Optional[str] = None,
    parent_uri: Optional[str] = None,
):
    """Registers a pre-existing group."""
    namespace, name = utils.canonicalize_ns_name_uri(
        namespace=namespace, name=name, dest_uri=dest_uri
    )

    if not name:
        # Extract the basename from the storage URI and use it for the name.
        parsed_uri = urllib.parse.urlparse(storage_uri)
        name = posixpath.basename(parsed_uri.path)

    groups_client = client.build(api_v2.GroupsApi)
    groups_client.register_group(
        group_namespace=namespace,
        x_tiledb_cloud_access_credentials_name=credentials_name,
        group_registration=api_v2.GroupRegistrationRequest(
            group_details=api_v2.GroupRegistrationRequestGroupDetails(
                name=name,
                uri=storage_uri,
                access_credentials_name=credentials_name,
                parent=parent_uri,
            )
        ),
    )
    if parent_uri:
        _add_to(namespace=namespace, name=name, parent_uri=parent_uri)


def info(uri: str) -> object:
    """Gets metadata about the named TileDB Cloud group."""
    namespace, group_name = utils.split_uri(uri)
    groups_client = client.build(rest_api.GroupsApi)
    return groups_client.get_group(group_namespace=namespace, group_name=group_name)


def contents(
    uri: str,
    async_req: bool = None,
    page: int = None,
    per_page: int = None,
    namespace: str = None,
    search: str = None,
    orderby: str = None,
    tag: list[str] = None,
    exclude_tag: list[str] = None,
    member_type: list[str] = None,
    exclude_member_type: list[str] = None,
) -> rest_api.GroupContents:
    """Get a group's contents.

    :param async_req bool: execute request asynchronously
    :param int page: pagination offset for assets
    :param int per_page: pagination limit for assets
    :param str namespace: namespace to search for
    :param str search: search string that will look at name, namespace
        or description fields
    :param str orderby: sort by which field valid values include
        last_accessed, size, name
    :param list[str] tag: tag to search for, more than one can be
        included
    :param list[str] exclude_tag: tags to exclude matching array in
        results, more than one can be included
    :param list[str] member_type: member type to search for, more than
        one can be included
    :param list[str] exclude_member_type: member type to exclude
        matching groups in results, more than one can be included
    :return: GroupContents
        If the method is called asynchronously, returns the request
        thread.
    """
    namespace, group_name = utils.split_uri(uri)
    groups_client = client.build(rest_api.GroupsApi)
    return groups_client.get_group_contents(
        group_namespace=namespace,
        group_name=group_name,
        async_req=async_req,
        page=page,
        per_page=per_page,
        namespace=namespace,
        search=search,
        orderby=orderby,
        tag=tag,
        exclude_tag=exclude_tag,
        member_type=member_type,
        exclude_member_type=exclude_member_type,
    )


def update_info(
    uri: str,
    *,
    description: Optional[str] = None,
    name: Optional[str] = None,
    logo: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> None:
    """
    Update Group Attributes

    :param uri: URI of the group in the form 'tiledb://<namespace>/<group>'
    :param description: Group description, defaults to None
    :param name: Group's name, defaults to None
    :param logo: Group's logo, defaults to None
    :param tags: Group tags, defaults to None
    :return: None
    """
    namespace, group_name = utils.split_uri(uri)
    groups_v1_client = client.build(rest_api.GroupsApi)
    info = {}
    for kw, arg in inspect.signature(update_info).parameters.items():
        if arg.kind != inspect.Parameter.KEYWORD_ONLY:
            # Skip every non-keyword-only argument
            continue

        value = locals()[kw]
        if value is None:
            # Explicitly update metadata
            continue
        info[kw] = value

    info = group_update.GroupUpdate(**info)
    try:
        return groups_v1_client.update_group(namespace, group_name, group_update=info)
    except rest_api.ApiException as exc:
        raise tiledb_cloud_error.maybe_wrap(exc)


def deregister(
    uri: str,
    *,
    recursive: bool = False,
) -> None:
    """Deregisters the given group from TileDB Cloud.

    :param uri: The URI of the group to deregister.
    :param recursive: If true, deregister the group recursively by deregistering
        all of the elements of the group (and all elements of those groups,
        recursively) before deregistering the group itself.
    """
    namespace, name = utils.split_uri(uri)
    groups_api = client.build(api_v2.GroupsApi)
    # Server expects recursive: "true"/"false".
    groups_api.deregister_group(
        group_namespace=namespace,
        group_name=name,
        recursive=str(bool(recursive)).lower(),
    )


def delete(uri: str, recursive: bool = False) -> None:
    """
    Deletes a group.

    :param uri: TileDB Group URI.
    :param recursive: Delete all off the group's contents, defaults to False
    """
    namespace, group_name = utils.split_uri(uri)
    groups_api = client.build(api_v2.GroupsApi)
    # Server expects recursive: "true"/"false".
    groups_api.delete_group(
        group_namespace=namespace,
        group_name=group_name,
        recursive=str(bool(recursive)).lower(),
    )


def _add_to(*, namespace: str, name: str, parent_uri: str) -> None:
    parent_ns, parent_name = utils.split_uri(parent_uri)
    client.build(api_v2.GroupsApi).update_group_contents(
        group_namespace=parent_ns,
        group_name=parent_name,
        group_update_contents=api_v2.GroupContentsChangesRequest(
            group_changes=api_v2.GroupContentsChangesRequestGroupChanges(
                members_to_add=[
                    api_v2.GroupMember(
                        name=name,
                        uri=f"tiledb://{namespace}/{name}",
                        type="GROUP",
                    ),
                ],
            ),
        ),
    )
