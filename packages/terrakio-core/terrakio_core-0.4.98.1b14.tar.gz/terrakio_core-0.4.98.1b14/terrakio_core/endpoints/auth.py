import json
import os
from typing import Any, Dict

from ..exceptions import (
    APIKeyError,
    AuthenticationExpireError,
    InvalidUsernamePasswordError,
    LoginError,
    QuotaError,
    RefreshAPIKeyError,
    ResetPasswordError,
    SignupError,
    UserInfoError,
    InvalidEmailFormatError,
    EmailAlreadyExistsError,
)
from ..helper.decorators import require_api_key, require_auth, require_token

class AuthClient:
    def __init__(self, client):
        self._client = client

    async def signup(self, email: str, password: str) -> Dict[str, str]:
        """
        Signup a new user with email and password.

        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing the authentication token
            
        Raises:
            SignupError: If the signup request fails
        """
        payload = {
            "email": email,
            "password": password
        }
        response, status = await self._client._terrakio_request("POST", "/users/signup", json=payload)
        if status != 200:
            if status == 422:
                raise InvalidEmailFormatError(f"Invalid email format: {response}", status_code=status)
            elif status == 409:
                raise EmailAlreadyExistsError(f"Email already exists: {response}", status_code=status)
            raise SignupError(f"Signup request failed: {response}", status_code=status)
        else:
            return response

    async def login(self, email: str, password: str) -> None:
        """
        Login a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            None
            
        Raises:
            APIError: If the login request fails
        """
        payload = {
            "email": email,
            "password": password
        }
        response, status = await self._client._terrakio_request("POST", "/users/login", json=payload)
        if status != 200:
            if status == 401:
                raise InvalidUsernamePasswordError(f"Invalid username or password: {response}", status_code=status)
            else:
                raise LoginError(f"Login request failed: {response}", status_code=status)
        else:
            token_response = response.get("token")
            
            if token_response:
                self._client.token = token_response

                api_key_response = await self.view_api_key()
                self._client.key = api_key_response
 
                if not self._client.url:
                    self._client.url = "https://api.terrak.io"
                
                self._save_config(email, token_response)
                
                self._client.logger.info(f"Successfully authenticated as: {email}")
                self._client.logger.info(f"Using Terrakio API at: {self._client.url}")
                

    @require_token
    async def view_api_key(self) -> str:
        """
        View the current API key for the authenticated user.
        
        Returns:
            str: The API key
            
        Raises:
            AuthenticationExpireError: If authentication expired
            APIKeyError: If the API key request fails
        """
        response, status = await self._client._terrakio_request("GET", "/users/key")
        api_key = response.get("apiKey")
        if status != 200:
            if status == 400 and response.get("detail")["message"] == "Not authenticated":
                raise AuthenticationExpireError(f"Authentication expired, please login again: {response}")
            else:
                raise APIKeyError(f"Error fetching API key: {response}", status_code=status)
        else:
            return api_key

    @require_api_key
    @require_token
    async def refresh_api_key(self) -> str:
        """
        Refresh the API key for the authenticated user.
        
        Returns:
            str: The new API key
            
        Raises:
            RefreshAPIKeyError: If the API key refresh request fails
        """
        response, status = await self._client._terrakio_request("POST", "/users/refresh_key")
        self._client.key = response.get("apiKey")
        if status != 200:
            raise RefreshAPIKeyError(f"Error refreshing API key: {response}", status_code=status)
        else:
            self._update_config_key()
            return self._client.key

    @require_api_key
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            Dict[str, Any]: User information
            
        Raises:
            AuthenticationExpireError: If authentication expired
            UserInfoError: If the user info request fails
        """
        response, status = await self._client._terrakio_request("GET", "/users/info")
        if status != 200:
            if status == 400 and response.get("detail")["message"] == "Not authenticated":
                raise AuthenticationExpireError(f"Authentication expired, please login again: {response}", status_code=status)
            else:
                raise UserInfoError(f"Error fetching user info: {response}", status_code=status)
        else:
            return response
    
    @require_api_key
    async def reset_password(self, email : str) -> Dict[str, Any]:
        """
        Reset the password for a user by email.
        """
        response, status = await self._client._terrakio_request("GET", f"/users/reset-password?email={email}")
        if status != 200:
            raise ResetPasswordError(f"Error resetting password: {response}", status_code=status)
        else:
            return response['message']

    @require_api_key
    async def get_user_quota(self):
        """
        Get the user's quota.

        Returns:
            Dict: User's quota

        Raises:
            QuotaError: If the quota request fails
        """
        response, status = await self._client._terrakio_request("GET", "/users/quota")
        if status != 200:
            raise QuotaError(f"Error fetching quota: {response}", status_code = status)
        else:
            return response

    def _save_config(self, email: str, token: str):
        """
        Helper method to save config file.
        
        Args:
            email: User's email address
            token: Authentication token
        """
        config_path = os.path.join(os.environ.get("HOME", ""), ".tkio_config.json")
        
        try:
            config = {"EMAIL": email, "TERRAKIO_API_KEY": self._client.key}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
            config["EMAIL"] = email
            config["TERRAKIO_API_KEY"] = self._client.key
            config["PERSONAL_TOKEN"] = token
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            self._client.logger.info(f"API key saved to {config_path}")
            
        except Exception as e:
            self._client.logger.info(f"Warning: Failed to update config file: {e}")

    def _update_config_key(self):
        """
        Helper method to update just the API key in config.
        """
        config_path = os.path.join(os.environ.get("HOME", ""), ".tkio_config.json")
        
        try:
            config = {"EMAIL": "", "TERRAKIO_API_KEY": ""}
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
            config["TERRAKIO_API_KEY"] = self._client.key
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            self._client.logger.info(f"API key updated in {config_path}")
            
        except Exception as e:
            self._client.logger.info(f"Warning: Failed to update config file: {e}")