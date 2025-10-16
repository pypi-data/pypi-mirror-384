"""Runtime errors for Nexa SDK operations."""


class NexaRuntimeError(Exception):
    """Base class for Nexa runtime errors."""
    
    def __init__(self, message: str, error_code: int = None):
        self.error_code = error_code
        super().__init__(message)


class ContextLengthExceededError(NexaRuntimeError):
    """Raised when the input context length exceeds the model's maximum."""
    
    def __init__(self, message: str = "Input context length exceeded model's maximum", error_code: int = None):
        super().__init__(message, error_code)


class GenerationError(NexaRuntimeError):
    """Raised when generation fails."""
    
    def __init__(self, message: str = "Generation failed", error_code: int = None):
        super().__init__(message, error_code)

