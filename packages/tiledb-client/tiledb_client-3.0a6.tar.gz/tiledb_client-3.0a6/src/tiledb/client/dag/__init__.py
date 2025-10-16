from types import MappingProxyType

from tiledb.client.dag import dag
from tiledb.client.dag import mode
from tiledb.client.dag import status

# Globals
MIN_BATCH_RESOURCES = MappingProxyType({"cpu": "1", "memory": "2Gi"})

# Re-exports.
Mode = mode.Mode
DAG = dag.DAG
Node = dag.Node
Status = status.Status
TGUDFStorage = dag.models.TGUDFStorage

list_logs = dag.list_logs
server_logs = dag.server_logs


__all__ = (
    "DAG",
    "MIN_BATCH_RESOURCES",
    "Mode",
    "Node",
    "Status",
    "list_logs",
    "server_logs",
)
