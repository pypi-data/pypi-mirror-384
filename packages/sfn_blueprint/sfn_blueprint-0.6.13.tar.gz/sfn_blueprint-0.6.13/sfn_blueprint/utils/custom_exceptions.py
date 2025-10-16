class RetryLimitExceededError(Exception):
    """Exception raised when the maximum retry limit is exceeded."""
    def __init__(self, message: str):
        super().__init__(message)


class TemplateValidationError(ValueError):
    """Custom exception for template validation failures"""
    pass