from typing import Dict, Any, List, Optional
from ..helper.decorators import require_token, require_api_key, require_auth

class UserManagement:
    def __init__(self, client):
        self._client = client

    @require_api_key
    def get_user_by_id(self, id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID
        
        Returns:
            User information
            
        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", f"admin/users/{id}")
    
    @require_api_key
    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Get user by email.

        Args:
            email: User email
        
        Returns:
            User information
            
        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", f"admin/users/email/{email}")
    
    @require_api_key
    def list_users(self, substring: Optional[str] = None, uid: bool = False) -> List[Dict[str, Any]]:
        """
        List users, optionally filtering by a substring.
        
        Args:
            substring: Optional substring to filter users
            uid: If True, includes the user ID in the response (default: False)
        
        Returns:
            List of users
            
        Raises:
            APIError: If the API request fails
        """
        params = {"uid": str(uid).lower()}
        if substring:
            params['substring'] = substring
        return self._client._terrakio_request("GET", "admin/users", params=params)
    
    @require_api_key
    def edit_user(
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
            APIError: If the API request fails
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
        return self._client._terrakio_request("PATCH", "admin/users", json=payload)
    
    @require_api_key
    def reset_quota(self, email: str, quota: Optional[int] = None) -> Dict[str, Any]:
        """
        Reset the quota for a user by email.
        
        Args:
            email: The user's email (required)
            quota: The new quota value (optional)
            
        Returns:
            API response as a dictionary
        """
        payload = {"email": email}
        if quota is not None:
            payload["quota"] = quota
        return self._client._terrakio_request("PATCH", f"admin/users/reset_quota/{email}", json=payload)
    
    @require_api_key
    def delete_user(self, uid: str) -> Dict[str, Any]:
        """
        Delete a user by UID.

        Args:
            uid: The user's UID (required)
            
        Returns:
            API response as a dictionary
            
        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("DELETE", f"admin/users/{uid}")