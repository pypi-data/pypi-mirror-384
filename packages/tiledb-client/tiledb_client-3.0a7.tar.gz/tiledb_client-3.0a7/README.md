# tiledb-client

The next generation Python client for TileDB.

This project provides a `tiledb.client` module and a `tiledb.cloud` module. The
latter provides some backwards compatibility by re-exporting `tiledb.client`
names from the `tiledb.cloud` namespaces. Installing the tiledb-client package
installs both those modules.

tiledb-client is incompatible with tiledb-cloud versions < 1 (all versions on
PyPI). Avoid installing tiledb-cloud in Python environments where tiledb-client
wil be installed.

## Installation

`pip install tiledb-client`

## Quickstart

```python
import tiledb.client

# First, configure your credentials (this saves them to a profile)
tiledb.client.configure(
    username="USERNAME",
    password="PASSWORD",
    workspace="WORKSPACE"
)

# Then login using the stored credentials
tiledb.client.login()

# Now you can use TileDB Client
tiledb.client.teamspaces.list_teamspaces()
```
