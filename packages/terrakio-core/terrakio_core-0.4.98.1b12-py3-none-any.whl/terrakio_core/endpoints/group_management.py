from typing import Dict, Any

from ..helper.decorators import require_token, require_api_key, require_auth
from ..exceptions import (
    ListGroupsError,
    GetGroupError,
    GetGroupDatasetsError,
    NoDatasetsFoundForGroupError,
    CreateGroupError,
    DeleteGroupError,
    AddUserToGroupError,
    AddGroupToDatasetError,
    AddUserToDatasetError,
    RemoveUserFromGroupError,
    RemoveUserFromDatasetError,
    GroupNotFoundError,
    GroupPermissionError,
    CommandPermissionError,
    UserNotFoundError,
    DatasetNotFoundError,
    RemoveGroupFromDatasetError,
)

class GroupManagement:
    """Base class with common group management methods."""
    def __init__(self, client):
        self._client = client

    @require_api_key
    async def get_group_datasets(self, group: str, collection: str = "terrakio-datasets") -> Dict[str, Any]:
        """
        Get datasets of a group.

        Args:
            group: Name of the group
            collection: Name of the collection (default is "terrakio-datasets")

        Returns:
            API response data

        Raises:
            GetGroupDatasetsError: If the API request fails
        """
        params = {"collection": collection}
        response, status = await self._client._terrakio_request("GET", f"/groups/{group}/datasets", params=params)
        if status != 200:
            if status == 404:
                raise NoDatasetsFoundForGroupError(f"No datasets found for group {group}", status_code = status)
            raise GetGroupDatasetsError(f"Get group datasets failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def add_user_to_dataset(self, dataset: str, emails: list[str]) -> Dict[str, Any]:
        """
        Add a user to a dataset.

        Args:
            dataset: Name of the dataset
            email: List of user emails to add to the dataset

        Returns:    
            API response data

        Raises:
            UserNotFoundError: If the user is not found
            DatasetNotFoundError: If the dataset is not found
            AddUserToDatasetError: If the API request fails
        """
        payload = {"emails": emails}
        response, status = await self._client._terrakio_request("POST", f"/datasets/{dataset}/share", json = payload)
        if status != 200:
            if status == 404:
                detail = response.get("detail", "")
                if "User" in detail and "not found" in detail:
                    raise UserNotFoundError(detail, status_code = status)
                elif "Dataset" in detail and "not found" in detail:
                    raise DatasetNotFoundError(detail, status_code = status)
            raise AddUserToDatasetError(f"Add user to dataset failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def add_user_to_group(self, group: str, emails: list[str]) -> Dict[str, Any]:
        """
        Add a user to a group.

        Args:
            group: Name of the group
            email: List of user emails to add to the group

        Returns:
            API response data

        Raises:
            UserNotFoundError: If the user is not found
            GroupNotFoundError: If the group is not found
            AddUserToGroupError: If the API request fails
        """
        payload = {"emails": emails}
        response, status = await self._client._terrakio_request("POST", f"/groups/{group}/users", json = payload)
        if status != 200:
            if status == 404:
                detail = response.get("detail", "")
                if "User" in detail:
                    raise UserNotFoundError(detail, status_code = status)
                elif "Group" in detail:
                    raise GroupNotFoundError(detail, status_code = status)
            raise AddUserToGroupError(f"Add user to group failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def remove_user_from_group(self, group: str, emails: list[str]) -> Dict[str, Any]:
        """
        Remove a user from a group.

        Args:
            group: Name of the group
            email: List of user emails to remove from the group

        Returns:
            API response data

        Raises:
            UserNotFoundError: If the user is not found
            GroupNotFoundError: If the group is not found
            RemoveUserFromGroupError: If the API request fails
        """
        payload = {"emails": emails}
        response, status = await self._client._terrakio_request("DELETE", f"/groups/{group}/users", json = payload)
        if status != 200:
            if status == 404:
                detail = response.get("detail", "")
                if "User" in detail:
                    raise UserNotFoundError(detail, status_code = status)
                elif "Group" in detail:
                    raise GroupNotFoundError(detail, status_code = status)
            raise RemoveUserFromGroupError(f"Remove user from group failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def add_group_to_dataset(self, dataset: str, id: str) -> Dict[str, Any]:
        """
        Add a group to a dataset.

        Args:
            dataset: Name of the dataset
            id: Group ID

        Returns:
            API response data

        Raises:
            AddGroupToDatasetError: If the API request fails
            DatasetNotFoundError: If the dataset is not found
            GroupNotFoundError: If the group is not found
        """
        payload = {"id": id}
        response, status = await self._client._terrakio_request("POST", f"/datasets/{dataset}/groups", json = payload)
        if status != 200:
            if status == 404:
                if "Dataset" in response.get("detail", ""):
                    raise DatasetNotFoundError(response.get("detail", ""), status_code = status)
                elif "Group" in response.get("detail", ""):
                    raise GroupNotFoundError(response.get("detail", ""), status_code = status)
            raise AddGroupToDatasetError(f"Add group to dataset failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def remove_group_from_dataset(self, dataset: str, id: str) -> Dict[str, Any]:
        """
        Remove a group from a dataset.

        Args:
            dataset: Name of the dataset
            id: Group ID

        Returns:
            API response data

        Raises:
            RemoveGroupFromDatasetError: If the API request fails
            DatasetNotFoundError: If the dataset is not found
            GroupNotFoundError: If the group is not found
        """
        payload = {"id": id}
        response, status = await self._client._terrakio_request("DELETE", f"/datasets/{dataset}/groups", json = payload)
        if status != 200:
            if status == 404:
                if "Dataset" in response.get("detail", ""):
                    raise DatasetNotFoundError(response.get("detail", ""), status_code = status)
                elif "Group" in response.get("detail", ""):
                    raise GroupNotFoundError(response.get("detail", ""), status_code = status)
            raise RemoveGroupFromDatasetError(f"Remove group from dataset failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def remove_user_from_dataset(self, dataset: str, emails: list[str]) -> Dict[str, Any]:
        """
        Remove a user from a dataset.

        Args:
            dataset: Name of the dataset
            email: List of user emails to remove from the dataset

        Returns:
            API response data

        Raises:
            UserNotFoundError: If the user is not found
            DatasetNotFoundError: If the dataset is not found
            RemoveUserFromDatasetError: If the API request fails
        """
        payload = {"emails": emails}
        response, status = await self._client._terrakio_request("PATCH", f"/datasets/{dataset}/share", json = payload)
        if status != 200:
            if status == 404:
                detail = response.get("detail", "")
                if "User" in detail and "not found" in detail:
                    raise UserNotFoundError(detail, status_code = status)
                elif "Dataset" in detail and "not found" in detail:
                    raise DatasetNotFoundError(detail, status_code = status)
            raise RemoveUserFromDatasetError(f"Remove user from dataset failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def list_groups(self) -> Dict[str, Any]:
        """
        List all groups.

        Returns:
            API response data

        Raises:
            GroupNotFoundError: If no group is linked to the current account
            ListGroupsError: If the API request fails
        """
        response, status = await self._client._terrakio_request("GET", "/groups")
        if status != 200:
            if status == 404:
                raise GroupNotFoundError(f"No group is linked to the current account", status_code = status)
            raise ListGroupsError(f"List groups failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def list_groups_admin(self) -> Dict[str, Any]:
        """
        List all groups (admin scope).

        Returns:
            API response data

        Raises:
            GroupNotFoundError: If no group is found
            CommandPermissionError: If the user does not have permission to list groups
            ListGroupsError: If the API request fails
        """
        response, status = await self._client._terrakio_request("GET", "/admin/groups")
        if status != 200:
            if status == 404:
                raise GroupNotFoundError("No group is found", status_code = status)
            if status == 403:
                raise CommandPermissionError(f"You do not have permission to list groups", status_code = status)
            raise ListGroupsError(f"List groups failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def get_group(self, group: str) -> Dict[str, Any]:
        """
        Get a group.

        Args:
            group: Name of the group

        Returns:
            API response data

        Raises:
            GroupNotFoundError: If the group is not found
            GetGroupError: If the API request fails
        """
        response, status = await self._client._terrakio_request("GET", f"/groups/{group}")
        if status != 200:
            if status == 404:
                raise GroupNotFoundError(f"Group {group} not found", status_code = status)
            elif status == 403:
                raise GroupPermissionError(f"You do not have permission to get group {group}", status_code = status)
            raise GetGroupError(f"Get group failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def get_group_admin(self, group_id: str) -> Dict[str, Any]:
        """
        Get a group (admin scope).

        Args:
            group_id: ID of the group

        Returns:
            API response data

        Raises:
            GroupNotFoundError: If the group is not found
            GetGroupError: If the API request fails
        """
        response, status = await self._client._terrakio_request("GET", f"/admin/groups/{group_id}")
        if status != 200:
            if status == 404:
                raise GroupNotFoundError(f"Group {group_id} not found", status_code = status)
            raise GetGroupError(f"Get group failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def create_group(self, name: str) -> Dict[str, Any]:
        """
        Create a group

        Args:
            name: Name of the group

        Returns:
            API response data

        Raises:
            CreateGroupError: If the API request fails
        """
        payload = {"name": name}
        response, status = await self._client._terrakio_request("POST", "/groups", json = payload)
        if status != 200:
            raise CreateGroupError(f"Create group failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def create_group_admin(self, name: str, owner: str) -> Dict[str, Any]:
        """
        Create a group (admin scope).

        Args:
            name: Name of the group
            owner: User email of the owner

        Returns:
            API response data

        Raises:
            CommandPermissionError: If the user does not have permission to create a group
            UserNotFoundError: If the user is not found
            CreateGroupError: If the API request fails
        """
        payload = {"name": name, "owner": owner}
        response, status = await self._client._terrakio_request("POST", f"/admin/groups", json=payload)
        if status != 200:
            if status == 403:
                raise CommandPermissionError(f"You do not have permission to create a group", status_code = status)
            elif status == 404:
                raise UserNotFoundError(f"User {owner} not found", status_code = status)
            raise CreateGroupError(f"Create group failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def delete_group(self, group: str) -> Dict[str, Any]:
        """
        Delete a group.

        Args:
            group: Name of the group to delete

        Returns:
            API response data

        Raises:
            GroupNotFoundError: If the group is not found
            GroupPermissionError: If the user does not have permission to delete the group
            DeleteGroupError: If the API request fails
        """
        response, status = await self._client._terrakio_request("DELETE", f"/groups/{group}")
        if status != 200:
            if status == 404:
                raise GroupNotFoundError(f"Group {group} not found", status_code = status)
            elif status == 403:
                raise GroupPermissionError(f"You do not have permission to delete group {group}", status_code = status)
            raise DeleteGroupError(f"Delete group failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def delete_group_admin(self, group: str) -> Dict[str, Any]:
        """
        Delete a group (admin scope).

        Args:
            group: Name of the group to delete

        Returns:
            API response data

        Raises:
            GroupNotFoundError: If the group is not found
            CommandPermissionError: If the user does not have permission to delete the group
            DeleteGroupError: If the API request fails
        """
        response, status = await self._client._terrakio_request("DELETE", f"/admin/groups/{group}")
        if status != 200:
            if status == 404:
                raise GroupNotFoundError(f"Group {group} not found", status_code = status)
            elif status == 403:
                raise CommandPermissionError(f"You do not have permission to delete group {group}", status_code = status)
            raise DeleteGroupError(f"Delete group failed with status {status}", status_code = status)
        else:
            return response