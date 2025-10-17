"""
WowMySQL Python SDK
Official client library for WowMySQL REST API v2
"""

from .client import WowMySQLClient, WowMySQLError
from .table import Table, QueryBuilder
from .types import (
    QueryOptions,
    FilterExpression,
    QueryResponse,
    CreateResponse,
    UpdateResponse,
    DeleteResponse,
    TableSchema,
    ColumnInfo,
)
from .storage import (
    WowMySQLStorage,
    StorageQuota,
    StorageFile,
    StorageError,
    StorageLimitExceededError,
)

__version__ = "0.2.0"
__all__ = [
    # Database Client
    "WowMySQLClient",
    "WowMySQLError",
    "Table",
    "QueryBuilder",
    # Types
    "QueryOptions",
    "FilterExpression",
    "QueryResponse",
    "CreateResponse",
    "UpdateResponse",
    "DeleteResponse",
    "TableSchema",
    "ColumnInfo",
    # Storage Client
    "WowMySQLStorage",
    "StorageQuota",
    "StorageFile",
    "StorageError",
    "StorageLimitExceededError",
]

