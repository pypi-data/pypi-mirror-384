from typing import Dict, Any, List, Optional
from ..helper.decorators import require_token, require_api_key, require_auth
from ..exceptions import UserNotFoundError, GetUserByIdError, GetUserByEmailError, ListUsersError, EditUserError, ResetQuotaError, DeleteUserError, GetUsersByRoleError, RoleDoNotExistError, ChangeRoleError

class UserManagement:
    def __init__(self, client):
        self._client = client

    @require_api_key
    async def get_user_by_id(self, id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID
        
        Returns:
            User information
            
        Raises:
            GetUserByIdError: If the API request fails
            UserNotFoundError: If the user is not found
        """
        response, status = await self._client._terrakio_request("GET", f"admin/users/{id}")
        if status != 200:
            if status == 404:
                raise UserNotFoundError(f"User {id} not found.", status_code = status)
            raise GetUserByIdError(f"Get user by id failed with status {status}", status_code = status)
        else:
            return response

    @require_api_key
    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Get user by email.

        Args:
            email: User email
        
        Returns:
            User information
            
        Raises:
            GetUserByEmailError: If the API request fails
            UserNotFoundError: If the user is not found
        """
        response, status = await self._client._terrakio_request("GET", f"admin/users/email/{email}")
        if status != 200:
            if status == 404:
                raise UserNotFoundError(f"User {email} not found.", status_code = status)
            raise GetUserByEmailError(f"Get user by email failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def list_users(self, substring: Optional[str] = None, uid: bool = False) -> List[Dict[str, Any]]:
        """
        List users, optionally filtering by a substring.
        
        Args:
            substring: Optional substring to filter users
            uid: If True, includes the user ID in the response (default: False)
        
        Returns:
            List of users
            
        Raises:
            ListUsersError: If the API request fails
        """
        params = {"uid": str(uid).lower()}
        if substring:
            params['substring'] = substring
        response, status = await self._client._terrakio_request("GET", "admin/users", params=params)
        if status != 200:
            raise ListUsersError(f"List users failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def edit_user(
        self,
        uid: str,
        email: Optional[str] = None,
        role: Optional[str] = None,
        apiKey: Optional[str] = None,
        groups: Optional[List[str]] = None,
        quota: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Edit user info. Only provided fields will be updated.
        
        Args:
            uid: User ID
            email: New user email
            role: New user role
            apiKey: New API key
            groups: New list of groups
            quota: New quota
        
        Returns:
            Updated user information
            
        Raises:
            EditUserError: If the API request fails
        """
        payload = {"uid": uid}
        payload_mapping = {
            "email": email,
            "role": role,
            "apiKey": apiKey,
            "groups": groups,
            "quota": quota
        }
        for key, value in payload_mapping.items():
            if value is not None:
                payload[key] = value
        response, status = await self._client._terrakio_request("PATCH", "admin/users", json=payload)
        if status != 200:
            raise EditUserError(f"Edit user failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def reset_quota(self, email: str, quota: Optional[int] = None) -> Dict[str, Any]:
        """
        Reset the quota for a user by email.
        
        Args:
            email: The user's email (required)
            quota: The new quota value (optional)
            
        Raises:
            ResetQuotaError: If the API request fails
        """
        payload = {"email": email}
        if quota is not None:
            payload["quota"] = quota
        response, status = await self._client._terrakio_request("PATCH", f"admin/users/reset_quota/{email}", json=payload)
        if status != 200:
            raise ResetQuotaError(f"Reset quota failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def delete_user(self, uid: str) -> Dict[str, Any]:
        """
        Delete a user by UID.

        Args:
            uid: The user's UID (required)
            
        Returns:
            Deleted user information
            
        Raises:
            DeleteUserError: If the API request fails
        """
        response, status = await self._client._terrakio_request("DELETE", f"admin/users/{uid}")
        if status != 200:
            raise DeleteUserError(f"Delete user failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def get_users_by_role(self, role: str) -> Dict[str, Any]:
        """
        Get users by role.

        Args:
            role: The user role to filter by (required)
            
        Returns:
            Users with the specified role
            
        Raises:
            GetUsersByRoleError: If the API request fails
        """
        response, status = await self._client._terrakio_request("GET", f"admin/users/role?role={role}")
        if status != 200:
            if status == 422:
                raise RoleDoNotExistError(f"Role {role} does not exist", status_code = status)
            raise GetUsersByRoleError(f"Get users by role failed with status {status}", status_code = status)
        else:
            return response
    
    @require_api_key
    async def change_role(self, uid: str, role: str, reset_quota: Optional[bool] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Change user role.

        Args:
            uid: The user's UID to change role for (required)
            role: Role to apply (required)
            reset_quota: Reset user's quota to new role limit (optional)
            limit: Quota limit if role is custom (optional)
            
        Returns:
            Response from the role change operation
            
        Raises:
            ChangeRoleError: If the API request fails
        """
        payload = {"uid": uid, "role": role}
        if reset_quota is not None:
            payload["reset_quota"] = reset_quota
        if limit is not None:
            payload["limit"] = limit
        response, status = await self._client._terrakio_request("PATCH", "admin/users/change_role", json=payload)
        if status != 200:
            if status == 404:
                raise UserNotFoundError(f"User {uid} not found", status_code = status)
            elif status == 422:
                raise RoleDoNotExistError(f"Role {role} does not exist", status_code = status)
            raise ChangeRoleError(f"Change role failed with status {status}", status_code = status)
        else:
            return response
