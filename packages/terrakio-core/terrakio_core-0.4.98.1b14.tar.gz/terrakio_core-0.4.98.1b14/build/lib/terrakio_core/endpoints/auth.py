import os
import json
from typing import Dict, Any
from ..exceptions import APIError
from ..helper.decorators import require_token, require_api_key, require_auth

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
            APIError: If the signup request fails
        """
        payload = {
            "email": email,
            "password": password
        }

        
        try:
            result = await self._client._terrakio_request("POST", "/users/signup", json=payload)
        except Exception as e:
            self._client.logger.info(f"Signup failed: {str(e)}")
            raise APIError(f"Signup request failed: {str(e)}")
            

    async def login(self, email: str, password: str) -> Dict[str, str]:
        """
        Login a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing the authentication token
            
        Raises:
            APIError: If the login request fails
        """
        payload = {
            "email": email,
            "password": password
        }
        
        try:
            result = await self._client._terrakio_request("POST", "/users/login", json=payload)
            token_response = result.get("token")
            
            if token_response:
                self._client.token = token_response

                api_key_response = await self.view_api_key()
                self._client.key = api_key_response
 
                if not self._client.url:
                    self._client.url = "https://api.terrak.io"
                
                self._save_config(email, token_response)
                
                self._client.logger.info(f"Successfully authenticated as: {email}")
                self._client.logger.info(f"Using Terrakio API at: {self._client.url}")
                
            return {"token": token_response} if token_response else {"error": "Login failed"}
            
        except Exception as e:
            self._client.logger.info(f"Login failed: {str(e)}")
            raise APIError(f"Login request failed: {str(e)}")

    @require_token
    async def view_api_key(self) -> str:
        """
        View the current API key for the authenticated user.
        
        Returns:
            str: The API key
            
        Raises:
            APIError: If the API request fails
        """
        result = await self._client._terrakio_request("GET", "/users/key")
        api_key = result.get("apiKey")
        return api_key

    @require_api_key
    @require_token
    async def refresh_api_key(self) -> str:
        """
        Refresh the API key for the authenticated user.
        
        Returns:
            str: The new API key
            
        Raises:
            APIError: If the API request fails
        """
        result = await self._client._terrakio_request("POST", "/users/refresh_key")
        self._client.key = result.get("apiKey")
                
        self._update_config_key()
        
        return self._client.key

    @require_api_key
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            Dict[str, Any]: User information
            
        Raises:
            APIError: If the API request fails
        """
        return self._client._terrakio_request("GET", "/users/info")

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


# we have four different circumstances:
# same expression, different region
# same expression, same region
# different expression, same region
# different expression, different region