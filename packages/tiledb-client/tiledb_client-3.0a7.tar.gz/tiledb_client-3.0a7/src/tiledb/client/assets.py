"""An Asset is an item in the TileDB Catalog.

An Asset may represent an Array, a Group of Arrays, a Folder, or a File.

When a Folder is created, it becomes an asset and a corresponded Asset
is created in the Catalog. When a file is uploaded, it becomes an asset.
Similarly, creation or registration of arrays and groups produces new
assets in the Catalog.



"""

import logging
import os.path
from typing import Any, Mapping, Optional, Sequence, Union
from urllib.parse import urlparse

import numpy
from typing_extensions import TypeAlias

import tiledb
from tiledb.datatypes import DataType

from . import client
from ._common.api_v4 import Asset
from ._common.api_v4 import AssetMemberType  # noqa: F401
from ._common.api_v4 import AssetMetadataSaveRequestInner
from ._common.api_v4 import AssetMetadataType
from ._common.api_v4 import AssetRegisterRequest
from ._common.api_v4 import AssetsApi
from ._common.api_v4 import AssetsMoveRequest
from ._common.api_v4 import AssetType
from ._common.api_v4 import AssetUpdateRequest
from ._common.api_v4 import Teamspace
from .pager import Pager
from .rest_api import ApiException
from .tiledb_cloud_error import maybe_wrap

logger = logging.getLogger(__name__)

AssetLike: TypeAlias = Union[Asset, str, object]
TeamspaceLike: TypeAlias = Union[Teamspace, str]


class AssetsError(tiledb.TileDBError):
    """Raised when assets can not be accessed."""


def _find_ids(
    teamspace: Union[Teamspace, str, None], asset: Union[Asset, str, object]
) -> tuple[str, str]:
    try:
        teamspace_id = getattr(teamspace, "teamspace_id", teamspace) or getattr(
            asset, "teamspace_id"
        )
        asset_id = getattr(asset, "asset_id", None) or getattr(asset, "id", asset)
        if not isinstance(teamspace_id, str):
            raise TypeError("teamspace_id was not a string.")
        if not isinstance(asset_id, str):
            raise TypeError("asset_id was not a string.")
    except (AttributeError, TypeError) as exc:
        raise AssetsError("An asset was not specified.") from exc
    else:
        return teamspace_id, asset_id


def list_assets(
    # Search is not implemented on server yet.
    search: Optional[str] = None,
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
    path: Optional[str] = "",
    type: Optional[str] = None,
    created_by: Optional[str] = None,
    expand: Optional[str] = None,
    page: Optional[int] = 1,
    per_page: Optional[int] = None,
    order_by: Optional[str] = None,
) -> Pager[Asset]:
    """List/search the Catalog for assets.

    An asset listing consists of a sequence of "pages", or
    batches, of lists of assets. This function returns a Pager object
    that represents one page of the listing. The object also serves as
    an iterator over all assets from that page to the last page, and it
    can be indexed to get all or a subset of assets from that page to
    the last page.

    Without parameters, this function will query all accessible assets,
    public or in private teamspaces that the user is a member of.

    Parameters
    ----------
    search : str
        Search keywords.
    teamspace : Teamspace or str, optional
        The teamspace to search within, specified by object or id.
    path : str, optional
        The path to search within. To list all assets in a teamspace,
        pass the empty string.
    type : str, optional
        Filters for assets of the specified type. Allowed types are
        enumerated by the AssetType class.
    created_by : str, optional
        Filters for assets created by a named user.
    expand : str, optional
        Specifies profiles of additional information
        to include in the response.
    page : int, optional
        Which page of results to retrieve. 1-based.
    per_page : int, optional
        How many results to include on each page.
    order_by : str, optional.
        The order to return assets, by default "created_at desc".
        Supported keys are "created_at", "name", and "asset_type".  They
        can be used alone or with "asc" or "desc" separated by a space
        (e.g. "created_at", "asset_type asc").

    Returns
    -------
    Pager for Assets

    Raises
    ------
    AssetsError
        Raised when assets can not be accessed.

    """

    if type is not None and type not in AssetType.allowable_values:
        raise AssetsError("Not a known asset type.")

    try:
        resp = Pager(
            client.client.build(AssetsApi).list_assets,
            client.get_workspace_id(),
            getattr(teamspace, "teamspace_id", teamspace),
            path,
            asset_type=type,
            created_by=created_by,
            per_page=per_page,
            expand=expand,
            order_by=order_by,
        )
        resp.call_page(page)
    except ApiException as exc:
        raise AssetsError("The asset listing request failed.") from exc
    else:
        return resp


def get_asset(
    asset: Union[object, str],
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
) -> Asset:
    """Retrieve the representation of an asset by object, path, or id.

    The catalog representation of a Folder, File, Array, or Group may be
    identified by its object representation, path relative to
    a teamspace, or asset id.

    Parameters
    ----------
    asset : Asset or str
        The target asset, specified by object, path, or id.
    teamspace : Teamspace or str, optional
        The teamspace to search within, specified by object or id. If
        not provided, the `asset` parameter is queried for a teamspace
        id.

    Returns
    -------
    Asset

    Raises
    ------
    AssetsError
        Raised when an asset representation cannot be retrieved.

    Examples
    --------
    >>> obj = get_asset(
    ...     "path/to/asset",
    ...     teamspace="teamspace_id",
    ... )

    """

    teamspace_id = (
        teamspace and getattr(teamspace, "teamspace_id", teamspace)
    ) or getattr(asset, "teamspace_id")
    asset_id = getattr(asset, "asset_id", asset)

    try:
        resp = client.client.build(AssetsApi).get_asset(
            client.get_workspace_id(),
            teamspace_id,
            asset_id,
        )
    except ApiException as exc:
        raise AssetsError("The asset retrieval request failed.") from exc
    else:
        return resp.data


def delete_metadata(
    asset: Union[object, str],
    keys: Sequence[str],
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
) -> None:
    """Delete asset metadata.

    Metadata are represented as a Python dict with string keys and
    values that can be any builtin Python type or Numpy scalar.

    Parameters
    ----------
    asset : obj or str
        The target asset, specified by object or id.
    keys : Sequence
        A sequence of keys to delete along with their values.
    teamspace : Teamspace or str, optional
        The teamspace to search within, specified by object or id. If
        not provided, the `asset` parameter is queried for a teamspace
        id.

    Returns
    -------
    None

    Raises
    ------
    AssetsError
        Raised when metadata can not be created and saved.

    Examples
    --------
    >>> delete_metadata(
    ...     "asset_id",
    ...     ["field1"],
    ...     teamspace="teamspace_id",
    ... )

    """

    teamspace_id = (
        teamspace and getattr(teamspace, "teamspace_id", teamspace)
    ) or getattr(asset, "teamspace_id")
    asset_id = getattr(asset, "asset_id", asset)

    try:
        client.client.build(AssetsApi).delete_asset_metadata(
            client.get_workspace_id(),
            teamspace_id,
            asset_id,
            list(keys),
        )
    except ApiException as exc:
        raise AssetsError("The asset metadata deletion request failed.") from exc


def update_metadata(
    asset: Union[object, str],
    items: Mapping[str, Any],
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
) -> None:
    """Update asset metadata.

    Metadata are represented as a Python dict with string keys and
    values that can be any builtin Python type or Numpy scalar.

    Parameters
    ----------
    asset : obj or str
        The target asset, specified by object or id.
    items : Mapping
        A mapping of metadata keys and values.
    teamspace : Teamspace or str, optional
        The teamspace to search within, specified by object or id. If
        not provided, the `asset` parameter is queried for a teamspace
        id.

    Returns
    -------
    None

    Raises
    ------
    AssetsError
        Raised when metadata can not be created and saved.

    Examples
    --------
    >>> update_metadata(
    ...     "asset_id",
    ...     {"field1": "another string", "field2": numpy.float64(4.2)},
    ...     teamspace="teamspace_id",
    ... )

    """

    teamspace_id = (
        teamspace and getattr(teamspace, "teamspace_id", teamspace)
    ) or getattr(asset, "teamspace_id")
    asset_id = getattr(asset, "asset_id", asset)
    metadata = [
        AssetMetadataSaveRequestInner(
            key=k,
            value=str(v),
            type=getattr(
                AssetMetadataType,
                DataType.from_numpy(numpy.array(v).dtype).tiledb_type.name,
            ),
        )
        for k, v in items.items()
    ]

    try:
        _ = client.client.build(AssetsApi).update_asset_metadata(
            client.get_workspace_id(),
            teamspace_id,
            asset_id,
            metadata,
        )
    except ApiException as exc:
        raise AssetsError("The asset metadata creation request failed.") from exc


def get_metadata(
    asset: Union[object, str],
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
) -> dict:
    """Retrieve asset metadata.

    Metadata are represented as a Python dict with string keys and
    values that can be any builtin Python type or Numpy scalar.

    Parameters
    ----------
    asset : obj or str
        The target asset, specified by object or id.
    teamspace : Teamspace or str, optional
        The teamspace to search within, specified by object or id. If
        not provided, the `asset` parameter is queried for a teamspace
        id.

    Returns
    -------
    dict

    Raises
    ------
    AssetsError
        Raised when metadata can not be created and saved.

    Examples
    --------
    >>> get_metadata("asset_id", teamspace="teamspace_id")

    """

    teamspace_id = (
        teamspace and getattr(teamspace, "teamspace_id", teamspace)
    ) or getattr(asset, "teamspace_id")
    asset_id = getattr(asset, "asset_id", asset)

    try:
        resp = client.client.build(AssetsApi).get_asset_metadata(
            client.get_workspace_id(),
            teamspace_id,
            asset_id,
        )
    except ApiException as exc:
        raise AssetsError("The asset metadata retrieval request failed.") from exc
    else:
        items = [
            (
                md.key,
                tiledb.datatypes.DataType.from_tiledb(
                    getattr(tiledb.datatypes.lt.DataType, md.type.upper())
                ).np_dtype.type(md.value),
            )
            for md in resp.data
        ]
        return dict(items)


def register_asset(
    teamspace: Union[Teamspace, str],
    uri: str,
    path: str,
    acn: Optional[str] = None,
) -> None:
    """Add a cloud storage object to the catalog, creating an asset.

    If `path` specifies a folder, the asset will be registered under
    the folder using the basename of `uri`.

    Parameters
    ----------
    teamspace : Teamspace or str
        The teamspace to which the object will be registered.
    uri : str
        Object identifier. For example: "s3://bucket/prefix/file".
    path : str
        The TileDB path at which the object will be registered.
    acn : str, optional
        The name of a stored credential for accessing the object.

    Returns
    -------
    None

    Raises
    ------
    AssetsError:
        If the registration failed.

    Examples
    --------
    >>> assets.register_asset(
    ...     "teamspace",
    ...     "s3://bucket/prefix/file",
    ...     "/file",
    ...     acn="bucket-credentials",
    ... )

    """
    teamspace_id = getattr(teamspace, "teamspace_id", teamspace)
    req = AssetRegisterRequest(uri=uri, access_credentials_name=acn)
    api = client.client.build(AssetsApi)
    try:
        api.register_asset(client.get_workspace_id(), teamspace_id, path, req)
    except ApiException as exc:
        # Is there a folder at path? If so, try again.
        ast: Asset = get_asset(path, teamspace=teamspace_id)
        if ast and ast.type == AssetType.FOLDER:
            logger.info("Registration targeting a folder: uri=%r, path=%r", uri, path)
            parsed = urlparse(uri)
            obj_basename = os.path.basename(parsed.path)
            req2 = AssetRegisterRequest(
                uri=uri,
                access_credentials_name=acn,
            )
            path = os.path.join(path, obj_basename)
            try:
                api.register_asset(client.get_workspace_id(), teamspace_id, path, req2)
            except ApiException as exc2:
                raise AssetsError("Registration of asset to a folder failed.") from exc2
        else:
            raise AssetsError("The asset registration request failed.") from exc


def update_asset(
    asset: Union[Asset, str, object],
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
    description: Optional[str] = None,
    name: Optional[str] = None,
) -> None:
    """Update the mutable properties of a asset.

    An asset can be renamed by updating its `name` property.

    The asset may be identified by asset id, path relative to
    a teamspace, or object representation (Asset instance).

    Presently, `description` is the only mutable property of a asset.

    Parameters
    ----------
    asset : Asset or str
        The representation or string identifier of an existing asset.
    description : str, optional
        Description of the asset.
    name : str, optional
        Name of the asset.
    teamspace : Teamspace or str, optional
        The representation or string identifier of the asset's
        teamspace. If the asset parameter is an Asset instance, the
        teamspace will be obtained from it.

    Returns
    -------
    None

    Raises
    ------
    AssetsError
        If the asset cannot be updated.

    Examples
    --------
    >>> assets.update_asset(
    ...     "asset1",
    ...     teamspace="teamspace",
    ...     name="new-name",
    ...     description="An updated description for asset one.",
    ... )

    """
    teamspace_id, asset_id = _find_ids(teamspace, asset)
    update_kwds = {}

    if description is not None:
        update_kwds.update(description=description, name=name)

    asset_update_request = AssetUpdateRequest(**update_kwds)

    try:
        client.client.build(AssetsApi).update_asset(
            client.get_workspace_id(),
            teamspace_id,
            asset_id,
            asset_update_request,
        )
    except ApiException as exc:
        raise AssetsError("The asset update request failed.") from exc


def move_assets(
    assets: Union[AssetLike, list[AssetLike]],
    folder: AssetLike,
    *,
    teamspace: Optional[Union[Teamspace, str]] = None,
) -> None:
    """Move one or more assets to a folder.

    This function can not be used to rename assets. For that, see
    `update_assets()`.

    Assets may be identified by asset id, path relative to
    a teamspace, or object representation (Asset instance).

    Parameters
    ----------
    assets : AssetLike or list of AssetLike
        The representation or string identifier(s) of an existing asset(s).
    folder : AssetLike
        The representation or string identifier of an existing folder.
    teamspace : Teamspace or str, optional
        The representation or string identifier of the assets'
        teamspace. If the folder parameter is an Asset instance, the
        teamspace will be obtained from it.

    Returns
    -------
    None

    Raises
    ------
    AssetsError
        If the assets cannot be moved.

    Examples
    --------
    >>> assets.move_assets(
    ...     "/asset1",
    ...     "/folder",
    ...     teamspace="teamspace",
    ... )

    """
    assets = [assets] if not isinstance(assets, list) else assets

    teamspace_id, folder_id = _find_ids(teamspace, folder)
    _, assets_to_add = zip(*(_find_ids(teamspace, ob) for ob in assets))
    assets_move_request = AssetsMoveRequest(
        assets_to_add=assets_to_add, target=folder_id
    )

    try:
        client.client.build(AssetsApi).move_assets(
            client.get_workspace_id(), teamspace_id, assets_move_request
        )
    except ApiException as exc:
        raise AssetsError("The assets move request failed.") from maybe_wrap(exc)


def delete_asset(
    asset: AssetLike,
    *,
    teamspace: Optional[TeamspaceLike] = None,
    delete_storage: Optional[bool] = False,
) -> None:
    """Remove an asset and its sub-assets from the TileDB catalog.

    The corresponding objects in cloud storage may be optionally deleted
    as well.

    The primary asset may be identified by its object representation,
    path relative to a teamspace, or asset id.

    Parameters
    ----------
    asset : AssetLike
        The target asset, specified by object, path, or id.
    teamspace : Teamspace or str, optional
        The teamspace to search within, specified by object or id. If
        not provided, the `asset` parameter is queried for a teamspace
        id.
    delete_storage : bool, optional
        If True, this function will also delete backing objects from
        storage (e.g., S3).  The default is False.

    Raises
    ------
    AssetsError
        Raised when an asset cannot be deleted.

    Examples
    --------
    >>> delete_asset(
    ...     "path/to/asset",
    ...     teamspace="teamspace_id",
    ... )

    """

    teamspace_id, asset_id = _find_ids(teamspace, asset)

    try:
        client.client.build(AssetsApi).delete_asset(
            client.get_workspace_id(),
            teamspace_id,
            asset_id,
            delete_assets="true" if delete_storage is True else "false",
        )
    except ApiException as exc:
        raise AssetsError("The asset deletion request failed.") from maybe_wrap(exc)
