"""Table and QueryBuilder classes."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from .types import (
    QueryOptions,
    FilterExpression,
    QueryResponse,
    CreateResponse,
    UpdateResponse,
    DeleteResponse,
)

if TYPE_CHECKING:
    from .client import WowMySQLClient


class QueryBuilder:
    """Fluent query builder for constructing database queries."""
    
    def __init__(self, client: "WowMySQLClient", table_name: str):
        self.client = client
        self.table_name = table_name
        self.options: QueryOptions = {}
    
    def select(self, columns: Union[str, List[str]]) -> "QueryBuilder":
        """
        Select specific columns.
        
        Args:
            columns: Column name(s) to select
            
        Returns:
            Self for chaining
        """
        if isinstance(columns, list):
            self.options["select"] = ",".join(columns)
        else:
            self.options["select"] = columns
        return self
    
    def filter(self, filter_expr: FilterExpression) -> "QueryBuilder":
        """
        Add a filter condition.
        
        Args:
            filter_expr: Filter expression
            
        Returns:
            Self for chaining
        """
        if "filter" not in self.options:
            self.options["filter"] = []
        
        current_filter = self.options["filter"]
        if isinstance(current_filter, list):
            current_filter.append(filter_expr)
        else:
            self.options["filter"] = [current_filter, filter_expr]
        
        return self
    
    def order(self, column: str, direction: str = "asc") -> "QueryBuilder":
        """
        Order results by column.
        
        Args:
            column: Column to order by
            direction: Sort direction ('asc' or 'desc')
            
        Returns:
            Self for chaining
        """
        self.options["order"] = column
        self.options["order_direction"] = direction
        return self
    
    def limit(self, limit: int) -> "QueryBuilder":
        """
        Limit number of results.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            Self for chaining
        """
        self.options["limit"] = limit
        return self
    
    def offset(self, offset: int) -> "QueryBuilder":
        """
        Skip records (pagination).
        
        Args:
            offset: Number of records to skip
            
        Returns:
            Self for chaining
        """
        self.options["offset"] = offset
        return self
    
    def get(self, additional_options: Optional[QueryOptions] = None) -> QueryResponse:
        """
        Execute the query.
        
        Args:
            additional_options: Additional query options
            
        Returns:
            Query response with data and metadata
        """
        final_options = {**self.options}
        if additional_options:
            final_options.update(additional_options)
        
        # Build query parameters
        params = {}
        
        if "select" in final_options:
            params["select"] = final_options["select"]
        
        if "filter" in final_options:
            filters = final_options["filter"]
            if isinstance(filters, list):
                filter_strs = []
                for f in filters:
                    filter_strs.append(f"{f['column']}.{f['operator']}.{f['value']}")
                params["filter"] = ",".join(filter_strs)
            else:
                f = filters
                params["filter"] = f"{f['column']}.{f['operator']}.{f['value']}"
        
        if "order" in final_options:
            params["order"] = final_options["order"]
            params["order_direction"] = final_options.get("order_direction", "asc")
        
        if "limit" in final_options:
            params["limit"] = final_options["limit"]
        
        if "offset" in final_options:
            params["offset"] = final_options["offset"]
        
        return self.client._request("GET", f"/{self.table_name}", params=params)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """
        Get first record matching query.
        
        Returns:
            First record or None
        """
        result = self.limit(1).get()
        return result["data"][0] if result["data"] else None


class Table:
    """Table interface for database operations."""
    
    def __init__(self, client: "WowMySQLClient", table_name: str):
        self.client = client
        self.table_name = table_name
    
    def select(self, columns: Union[str, List[str]]) -> QueryBuilder:
        """
        Start a query with column selection.
        
        Args:
            columns: Column(s) to select
            
        Returns:
            QueryBuilder for chaining
        """
        return QueryBuilder(self.client, self.table_name).select(columns)
    
    def filter(self, filter_expr: FilterExpression) -> QueryBuilder:
        """
        Start a query with a filter.
        
        Args:
            filter_expr: Filter expression
            
        Returns:
            QueryBuilder for chaining
        """
        return QueryBuilder(self.client, self.table_name).filter(filter_expr)
    
    def get(self, options: Optional[QueryOptions] = None) -> QueryResponse:
        """
        Get all records with optional filters.
        
        Args:
            options: Query options
            
        Returns:
            Query response
        """
        return QueryBuilder(self.client, self.table_name).get(options)
    
    def get_by_id(self, record_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a single record by ID.
        
        Args:
            record_id: Record ID
            
        Returns:
            Record data
        """
        return self.client._request("GET", f"/{self.table_name}/{record_id}")
    
    def create(self, data: Dict[str, Any]) -> CreateResponse:
        """
        Create a new record.
        
        Args:
            data: Record data
            
        Returns:
            Create response with new record ID
        """
        return self.client._request("POST", f"/{self.table_name}", json=data)
    
    def update(self, record_id: Union[int, str], data: Dict[str, Any]) -> UpdateResponse:
        """
        Update a record by ID.
        
        Args:
            record_id: Record ID
            data: Data to update
            
        Returns:
            Update response
        """
        return self.client._request("PATCH", f"/{self.table_name}/{record_id}", json=data)
    
    def delete(self, record_id: Union[int, str]) -> DeleteResponse:
        """
        Delete a record by ID.
        
        Args:
            record_id: Record ID
            
        Returns:
            Delete response
        """
        return self.client._request("DELETE", f"/{self.table_name}/{record_id}")

