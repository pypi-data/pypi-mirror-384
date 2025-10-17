from typing import Optional


class SAIError(Exception):
    """Base exception class for SAI-specific errors"""

    pass


class InternalError(SAIError):
    """Internal error that should not happen"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class ConfigurationError(SAIError):
    """Error raised when there is a problem with the configuration"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class AuthenticationError(SAIError):
    """Error raised when there is a problem with the authentication"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class NetworkError(SAIError):
    """Error raised when there is a problem with the network"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class CustomCodeError(SAIError):
    """Error raised when there is a problem with the custom code"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class ModelError(SAIError):
    """Error raised when there is a problem with the model"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class PackageError(SAIError):
    """Error raised when there is a problem with the package"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class SubmissionError(SAIError):
    """Error raised when there is a problem with the submission"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class BenchmarkError(SAIError):
    """Error raised when there is a problem with the benchmark"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class RecordingError(SAIError):
    """Error raised when there is a problem with recording an episode"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class CompetitionError(SAIError):
    """Error raised when there is a problem with the competition"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class SceneError(SAIError):
    """Error raised when there is a problem with the scene"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"        


class EnvironmentError(SAIError):
    """Error raised when there is a problem with the environment"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"


class SetupError(SAIError):
    """Error raised when there is a problem with the setup"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.cause = cause

    def __str__(self):
        return f"{self.message}"
