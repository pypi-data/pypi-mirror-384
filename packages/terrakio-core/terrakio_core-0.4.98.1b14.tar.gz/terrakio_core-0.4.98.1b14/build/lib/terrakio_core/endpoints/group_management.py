from typing import Dict, Any
from ..helper.decorators import require_token, require_api_key, require_auth
class BaseGroupManagement:
    """Base class with common group management methods."""
    def __init__(self, client):
        self._client = client

    @require_api_key
    def get_group_datasets(self, group: str, collection: str = "terrakio-datasets") -> Dict[str, Any]:
        """
        Get datasets of a group.

        Args:
            group: Name of the group
            collection: Name of the collection (default is "terrakio-datasets")

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        params = {"collection": collection}
        return self._client._terrakio_request("GET", f"/groups/{group}/datasets", params=params)

    @require_api_key
    def add_user_to_group(self, group: str, emails: list[str]) -> Dict[str, Any]:
        """
        Add a user to a group.

        Args:
            group: Name of the group
            email: List of user emails to add to the group

        Returns:
            API response data
        """
        payload = {"emails": emails}
        return self._client._terrakio_request("POST", f"/groups/{group}/users", json = payload)

    @require_api_key
    def add_group_to_dataset(self, dataset: str, id: str) -> Dict[str, Any]:
        """
        Add a group to a dataset.

        Args:
            dataset: Name of the dataset
            id: Group ID

        Returns:
            API response data
        """
        payload = {"id": id}
        return self._client._terrakio_request("POST", f"/datasets/{dataset}/groups", json = payload)

    @require_api_key
    def add_user_to_dataset(self, dataset: str, emails: list[str]) -> Dict[str, Any]:
        """
        Add a user to a dataset.

        Args:
            dataset: Name of the dataset
            email: List of user emails to add to the dataset

        Returns:
            API response data
        """
        payload = {"emails": emails}
        return self._client._terrakio_request("POST", f"/datasets/{dataset}/share", json = payload)

    @require_api_key
    def remove_user_from_group(self, group: str, emails: list[str]) -> Dict[str, Any]:
        """
        Remove a user from a group.

        Args:
            group: Name of the group
            email: List of user emails to remove from the group

        Returns:
            API response data
        """
        payload = {"emails": emails}
        return self._client._terrakio_request("DELETE", f"/groups/{group}/users", json = payload)
    
    @require_api_key
    def remove_user_from_dataset(self, dataset: str, emails: list[str]) -> Dict[str, Any]:
        """
        Remove a user from a dataset.

        Args:
            dataset: Name of the dataset
            email: List of user emails to remove from the dataset

        Returns:
            API response data
        """
        payload = {"emails": emails}
        return self._client._terrakio_request("PATCH", f"/datasets/{dataset}/share", json = payload)

class GroupManagement(BaseGroupManagement):
    """Normal user group management with regular user permissions."""
    @require_api_key
    def list_groups(self) -> Dict[str, Any]:
        """
        List all groups.

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", "/groups")
    
    @require_api_key
    def get_group(self, group: str) -> Dict[str, Any]:
        """
        Get a group.

        Args:
            group: Name of the group

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", f"/groups/{group}")

    @require_api_key
    def create_group(self, name: str) -> Dict[str, Any]:
        """
        Create a group

        Args:
            name: Name of the group

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        payload = {"name": name}
        return self._client._terrakio_request("POST", "/groups", json = payload)

    @require_api_key
    def delete_group(self, group: str) -> Dict[str, Any]:
        """
        Delete a group.

        Args:
            group: Name of the group to delete

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("DELETE", f"/groups/{group}")

class AdminGroupManagement(BaseGroupManagement):
    """Admin user group management with admin permissions."""
    @require_api_key
    def list_groups(self) -> Dict[str, Any]:
        """
        List all groups.

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", "/admin/groups")
    
    @require_api_key
    def get_group(self, group: str) -> Dict[str, Any]:
        """
        Get a group.

        Args:
            group: Name of the group

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", f"/admin/groups/{group}")
    
    @require_api_key
    def create_group(self, name: str, owner: str) -> Dict[str, Any]:
        """
        Create a group.

        Args:
            name: Name of the group
            owner: User email of the owner

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        payload = {"name": name, "owner": owner}
        return self._client._terrakio_request("POST", f"/admin/groups", json=payload)
    
    @require_api_key
    def delete_group(self, group: str) -> Dict[str, Any]:
        """
        Delete a group.

        Args:
            group: Name of the group to delete

        Returns:
            API response data

        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("DELETE", f"/admin/groups/{group}")