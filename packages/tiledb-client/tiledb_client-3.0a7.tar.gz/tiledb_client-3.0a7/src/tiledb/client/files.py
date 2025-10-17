"""TileDB File Assets

The functions of this module allow a TileDB File to be downloaded to a
local filesystem, or uploaded from a local filesystem to TileDB so that
it becomes a catalog asset.

"""

from typing import BinaryIO, Union

import tiledb
from tiledb.client import client
from tiledb.client._common.api_v4 import FilesApi
from tiledb.client.folders import Teamspace

from .rest_api import ApiException


class FilesError(tiledb.TileDBError):
    """Raised when a file transfer operation fails."""


def download_file(
    teamspace: Union[Teamspace, str],
    path: str,
    file: Union[BinaryIO, str],
) -> None:
    """Download a file from a teamspace.

    Parameters
    ----------
    teamspace : Teamspace or str
        The teamspace to which the downloaded file belongs.
    path : str
        The path of the file to be downloaded.
    file : BinaryIO or str
        The file to be written.

    Returns
    -------
    None

    Raises
    ------
    FilesError:
        If the file download failed.

    Examples
    --------
    >>> files.download_file(
    ...     "teamspace",
    ...     "README.md",
    ...     open("README.md", "wb"),
    ... )

    Notes
    -----
    The current implementation makes a copy of the file in memory
    before writing to the output file.

    """
    try:
        api_instance = client.client.build(FilesApi)
        resp = api_instance.file_get(
            client.get_workspace_id(),
            getattr(teamspace, "teamspace_id", teamspace),
            path,
            _preload_content=False,
        )
    except ApiException as exc:
        raise FilesError("The file download failed.") from exc
    else:
        file.write(resp.read())


def upload_file(
    teamspace: Union[Teamspace, str],
    file: Union[BinaryIO, str],
    path: str,
    content_type: str = "application/octet-stream",
) -> None:
    """Upload a file to a teamspace.

    Parameters
    ----------
    teamspace : Teamspace or str
        The teamspace to which the uploaded file will belong.
    file : BinaryIO or str
        The file to be uploaded.
    path : str
        The path of the file to create.
    content_type: str, optional
        The content type of the uploaded file.

    Returns
    -------
    None

    Raises
    ------
    FilesError:
        If the file upload failed.

    Examples
    --------
    >>> files.upload_file(
    ...     "teamspace",
    ...     open("README.md", "rb"),
    ...     "README.md",
    ...     content-type="text/markdown",
    ... )

    Notes
    -----
    The current implementation makes a copy of the file in memory
    before submiting it to the server.

    """
    try:
        api_instance = client.client.build(FilesApi)
        api_instance.api_client.set_default_header("Content-Type", content_type)
        api_instance.upload_part(
            client.get_workspace_id(),
            getattr(teamspace, "teamspace_id", teamspace),
            path,
            file.read(),
        )
        api_instance.api_client.default_headers.pop("Content-Type")
    except ApiException as exc:
        raise FilesError("The file upload failed.") from exc
