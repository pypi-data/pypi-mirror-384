class OneClickImpactError(Exception):
    """Custom exception for 1ClickImpact SDK errors."""
    
    def __init__(self, message, error_type=None):
        self.message = message
        self.error_type = error_type
        super().__init__(message)
