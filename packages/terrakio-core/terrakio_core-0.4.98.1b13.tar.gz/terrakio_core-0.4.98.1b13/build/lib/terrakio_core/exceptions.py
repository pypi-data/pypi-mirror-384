class APIError(Exception):
    """Exception raised for errors in the API responses."""
    
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class ConfigurationError(Exception):
    """Exception raised for errors in the configuration."""
    pass


class DownloadError(Exception):
    """Exception raised for errors during data download."""
    pass


class ValidationError(Exception):
    """Exception raised for invalid request parameters."""
    pass