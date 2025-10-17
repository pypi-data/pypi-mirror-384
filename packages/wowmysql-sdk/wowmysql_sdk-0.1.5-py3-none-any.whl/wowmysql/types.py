"""Type definitions for WowMySQL SDK."""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired


class FilterExpression(TypedDict):
    """Filter expression for queries."""
    column: str
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "like", "is"]
    value: Union[str, int, float, bool, None]


class QueryOptions(TypedDict, total=False):
    """Options for querying records."""
    select: NotRequired[Union[str, List[str]]]
    filter: NotRequired[Union[FilterExpression, List[FilterExpression]]]
    order: NotRequired[str]
    order_direction: NotRequired[Literal["asc", "desc"]]
    limit: NotRequired[int]
    offset: NotRequired[int]


class QueryResponse(TypedDict):
    """Response from a query operation."""
    data: List[Dict[str, Any]]
    count: int
    total: int
    limit: int
    offset: int


class CreateResponse(TypedDict):
    """Response from a create operation."""
    id: Union[int, str]
    message: str


class UpdateResponse(TypedDict):
    """Response from an update operation."""
    message: str
    affected_rows: int


class DeleteResponse(TypedDict):
    """Response from a delete operation."""
    message: str
    affected_rows: int


class ColumnInfo(TypedDict):
    """Column information in table schema."""
    name: str
    type: str
    nullable: bool
    key: str
    default: Any
    extra: str


class TableSchema(TypedDict):
    """Table schema information."""
    table: str
    columns: List[ColumnInfo]
    primary_key: Optional[str]

