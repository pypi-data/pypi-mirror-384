

class GenericXursparksException(Exception):
    """Custom exception for Xursparks Generic Errors."""
    pass

class ApiServiceException(Exception):
    """Custom exception for API service errors."""
    
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

    def __str__(self):
        return f"ApiServiceException: {self.args[0]} (Status Code: {self.status_code})" if self.status_code else f"ApiServiceException: {self.args[0]}"