"""HTTP client for accessing HumaLab service APIs with API key authentication."""

import os
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin


class HumaLabApiClient:
    """HTTP client for making authenticated requests to HumaLab service APIs."""
    
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None
    ):
        """
        Initialize the HumaLab API client.
        
        Args:
            base_url: Base URL for the HumaLab service (defaults to localhost:8000)
            api_key: API key for authentication (defaults to HUMALAB_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("HUMALAB_SERVICE_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("HUMALAB_API_KEY")
        self.timeout = timeout or 30.0  # Default timeout of 30 seconds
        
        # Ensure base_url ends without trailing slash
        self.base_url = self.base_url.rstrip('/')
        
        if not self.api_key:
            raise ValueError(
                "API key is required. Set HUMALAB_API_KEY environment variable "
                "or pass api_key parameter to HumaLabApiClient constructor."
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "HumaLab-SDK/1.0"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request to the HumaLab service.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be joined with base_url)
            data: JSON data for request body
            params: Query parameters
            files: Files for multipart upload
            **kwargs: Additional arguments passed to requests
            
        Returns:
            requests.Response object
            
        Raises:
            requests.exceptions.RequestException: For HTTP errors
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip('/'))
        headers = self._get_headers()
        
        # If files are being uploaded, don't set Content-Type (let requests handle it)
        if files:
            headers.pop("Content-Type", None)
        
        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            files=files,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )
        
        # Raise an exception for HTTP error responses
        response.raise_for_status()
        
        return response
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, **kwargs)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """Make a POST request."""
        return self._make_request("POST", endpoint, data=data, files=files, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """Make a PUT request."""
        return self._make_request("PUT", endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request."""
        return self._make_request("DELETE", endpoint, **kwargs)
    
    # Convenience methods for common API operations
    
    def get_resources(
        self, 
        resource_types: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        latest_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get list of all resources.
        
        Args:
            resource_types: Comma-separated resource types to filter by
            limit: Maximum number of resources to return
            offset: Number of resources to skip
            latest_only: If true, only return latest version of each resource
            
        Returns:
            Resource list with pagination info
        """
        params = {
            "limit": limit,
            "offset": offset,
            "latest_only": latest_only
        }
        if resource_types:
            params["resource_types"] = resource_types
            
        response = self.get("/resources", params=params)
        return response.json()
    
    def get_resource(self, name: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a specific resource.
        
        Args:
            name: Resource name
            version: Specific version (defaults to latest)
            
        Returns:
            Resource data
        """
        if version is not None:
            endpoint = f"/resources/{name}/{version}"
        else:
            endpoint = f"/resources/{name}"
        
        response = self.get(endpoint)
        return response.json()
    
    def download_resource(
        self, 
        name: str, 
        version: Optional[int] = None
    ) -> bytes:
        """
        Download a resource file.
        
        Args:
            name: Resource name
            version: Specific version (defaults to latest)
            
        Returns:
            Resource file content as bytes
        """
        if version is not None:
            endpoint = f"/resources/{name}/download?version={version}"
        else:
            endpoint = f"/resources/{name}/download"

        response = self.get(endpoint)
        return response.content
    
    def upload_resource(
        self, 
        name: str, 
        file_path: str, 
        resource_type: str,
        description: Optional[str] = None,
        filename: Optional[str] = None,
        allow_duplicate_name: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a resource file.
        
        Args:
            name: Resource name
            file_path: Path to file to upload
            resource_type: Type of resource (urdf, mjcf, etc.)
            description: Optional description
            filename: Optional custom filename
            allow_duplicate_name: Allow creating new version with existing name
            
        Returns:
            Created resource data
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            if description:
                data['description'] = description
            if filename:
                data['filename'] = filename
                
            params = {
                'resource_type': resource_type,
                'allow_duplicate_name': allow_duplicate_name
            }
            
            response = self.post(f"/resources/{name}/upload", files=files, params=params)
            return response.json()
    
    def get_resource_types(self) -> List[str]:
        """Get list of all available resource types."""
        response = self.get("/resources/types")
        return response.json()
    
    def delete_resource(self, name: str, version: Optional[int] = None) -> None:
        """
        Delete a resource.
        
        Args:
            name: Resource name
            version: Specific version to delete (if None, deletes all versions)
        """
        if version is not None:
            endpoint = f"/resources/{name}/{version}"
        else:
            endpoint = f"/resources/{name}"
        
        self.delete(endpoint)
    
    def get_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of all scenarios."""
        response = self.get("/scenarios")
        return response.json()
    
    def get_scenario(self, uuid: str, version: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a specific scenario.
        
        Args:
            uuid: Scenario UUID
            version: Specific version (defaults to latest)
            
        Returns:
            Scenario data
        """
        if version is not None:
            endpoint = f"/scenarios/{uuid}/{version}"
        else:
            endpoint = f"/scenarios/{uuid}"
        
        response = self.get(endpoint)
        return response.json()
