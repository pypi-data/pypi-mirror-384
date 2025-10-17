"""WowMySQL client implementation."""

import requests
from typing import List, Optional
from .table import Table
from .types import TableSchema


class WowMySQLError(Exception):
    """Base exception for WowMySQL SDK errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class WowMySQLClient:
    """
    WowMySQL client for interacting with your database via REST API.
    
    Example:
        >>> client = WowMySQLClient(
        ...     project_url="myproject",
        ...     api_key="your_api_key"
        ... )
        >>> users = client.table("users").get()
    """
    
    def __init__(
        self,
        project_url: str,
        api_key: str,
        base_domain: str = "wowmysql.com",
        secure: bool = True,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize WowMySQL client.
        
        Args:
            project_url: Project subdomain or full URL
                Examples:
                - Just slug: "myproject" (will construct URL automatically)
                - Full URL: "https://myproject.wowmysql.com/api"
            api_key: API key for authentication
            base_domain: Base domain (default: wowmysql.com)
            secure: Use HTTPS (default: True)
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Verify SSL certificates (default: True).
                Set to False for development/self-signed certs
        """
        # Build base URL
        if project_url.startswith("http://") or project_url.startswith("https://"):
            # Full URL provided
            self.base_url = project_url.rstrip('/')
            # Check if URL already contains /api - if so, don't add /api/v2
            if '/api' in self.base_url:
                # URL like: https://project.wowmysql.com/api
                # Remove /api from base and set api_url properly
                self.base_url = self.base_url.rsplit('/api', 1)[0]
                self.api_url = f"{self.base_url}/api/v2"
            else:
                # URL like: https://project.wowmysql.com
                self.api_url = f"{self.base_url}/api/v2"
        else:
            # Just slug provided: "project-slug"
            protocol = "https" if secure else "http"
            self.base_url = f"{protocol}://{project_url}.{base_domain}"
            self.api_url = f"{self.base_url}/api/v2"
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        
        # Configure SSL verification
        self.session.verify = verify_ssl
        
        # Suppress SSL warnings if verification is disabled
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None
    ) -> dict:
        """Make HTTP request to API."""
        url = f"{self.api_url}{path}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            raise WowMySQLError(
                error_data.get("detail", str(e)),
                status_code=e.response.status_code,
                response=error_data
            )
        except requests.exceptions.RequestException as e:
            raise WowMySQLError(str(e))
    
    def table(self, table_name: str) -> Table:
        """
        Get a table interface for fluent API.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table instance for the specified table
        """
        return Table(self, table_name)
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        response = self._request("GET", "/tables")
        return response["tables"]
    
    def get_table_schema(self, table_name: str) -> TableSchema:
        """
        Get table schema information.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table schema with columns and primary key
        """
        return self._request("GET", f"/tables/{table_name}/schema")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

