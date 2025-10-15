# terrakio_core/decorators.py
from functools import wraps
from ..exceptions import ConfigurationError

def require_token(func):
    """Decorator to ensure a token is available before a method can be executed."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check both direct token and client token
        has_token = False
        if hasattr(self, 'token') and self.token:
            has_token = True
        elif hasattr(self, '_client') and hasattr(self._client, 'token') and self._client.token:
            has_token = True
            
        if not has_token:
            raise ConfigurationError("Authentication token required. Please login first.")
        return func(self, *args, **kwargs)
    
    wrapper._is_decorated = True
    return wrapper

def require_api_key(func):
    """Decorator to ensure an API key is available before a method can be executed."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check both direct key and client key
        has_key = False
        if hasattr(self, 'key') and self.key:
            has_key = True
        elif hasattr(self, '_client') and hasattr(self._client, 'key') and self._client.key:
            has_key = True
            
        if not has_key:
            raise ConfigurationError("API key required. Please provide an API key or login first.")
        return func(self, *args, **kwargs)
    
    wrapper._is_decorated = True
    return wrapper

def require_auth(func):
    """Decorator that requires either a token OR an API key"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check both direct auth and client auth
        has_token = (hasattr(self, 'token') and self.token) or \
                   (hasattr(self, '_client') and hasattr(self._client, 'token') and self._client.token)
        has_api_key = (hasattr(self, 'key') and self.key) or \
                     (hasattr(self, '_client') and hasattr(self._client, 'key') and self._client.key)
        
        if not has_token and not has_api_key:
            raise ConfigurationError(
                "Authentication required. Please provide either an API key or login to get a token."
            )
        return func(self, *args, **kwargs)
    
    wrapper._is_decorated = True
    return wrapper