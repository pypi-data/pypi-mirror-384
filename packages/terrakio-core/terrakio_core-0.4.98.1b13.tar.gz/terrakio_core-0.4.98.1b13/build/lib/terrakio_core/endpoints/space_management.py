from typing import Dict, Any, Optional
from ..helper.decorators import require_token, require_api_key, require_auth
class SpaceManagement:
    def __init__(self, client):
        self._client = client

    @require_api_key
    def get_total_space_used(self) -> Dict[str, Any]:
        """
        Get total space used by the user.
        
        Returns:
            Dict[str, Any]: Total space used by the user.

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", "/users/jobs")

    @require_api_key
    def get_space_used_by_job(self, name: str, region: str) -> Dict[str, Any]:
        """
        Get space used by a specific job.

        Args:
            name: The name of the job
            region: The region of the job

        Returns:
            Dict[str, Any]: Space used by the job.
        
        Raises:
            APIError: If the API request fails
        """
        params = {"region": region}
        return self._client._terrakio_request("GET", f"/users/jobs/{name}", params=params)
    
    @require_api_key
    def delete_user_job(self, name: str, region: str) -> Dict[str, Any]:
        """
        Delete a user job by name and region.
        
        Args:
            name: The name of the job
            region: The region of the job
            
        Returns:
            Dict[str, Any]: Response from the delete operation.
        
        Raises:
            APIError: If the API request fails
        """
        params = {"region": region}
        return self._client._terrakio_request("DELETE", f"/users/jobs/{name}", params=params)

    @require_api_key
    def delete_data_in_path(self, path: str, region: str) -> Dict[str, Any]:
        """
        Delete data in a GCS path for a given region.
        
        Args:
            path: The GCS path to delete data from
            region: The region where the data is located
            
        Returns:
            Dict[str, Any]: Response from the delete operation.
        
        Raises:
            APIError: If the API request fails
        """
        params = {"path": path, "region": region}
        return self._client._terrakio_request("DELETE", "/users/jobs", params=params)