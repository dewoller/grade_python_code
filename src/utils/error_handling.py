"""Custom exceptions for the marking tool."""


class MarkingError(Exception):
    """Base exception for marking-related errors."""
    pass


class FileNotFoundError(MarkingError):
    """Raised when a required file is not found."""
    pass


class InvalidFileError(MarkingError):
    """Raised when a file is invalid or corrupted."""
    pass


class ParsingError(MarkingError):
    """Raised when parsing a file fails."""
    pass


class NotebookParsingError(ParsingError):
    """Raised when parsing a Jupyter notebook fails."""
    pass


class RubricParsingError(ParsingError):
    """Raised when parsing a rubric CSV fails."""
    pass


class TaskNotFoundError(MarkingError):
    """Raised when a required task is not found in the notebook."""
    
    def __init__(self, task_number: int, message: str = None):
        self.task_number = task_number
        if message is None:
            message = f"Task {task_number} not found in notebook"
        super().__init__(message)


class IncompleteCodeError(MarkingError):
    """Raised when code is incomplete or only contains placeholders."""
    
    def __init__(self, task_number: int, message: str = None):
        self.task_number = task_number
        if message is None:
            message = f"Task {task_number} contains incomplete code"
        super().__init__(message)


class APIError(MarkingError):
    """Raised when an API call fails."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class ModelError(MarkingError):
    """Raised when model loading or inference fails."""
    pass


class ConfigurationError(MarkingError):
    """Raised when configuration is invalid."""
    pass


class OutputGenerationError(MarkingError):
    """Raised when output generation fails."""
    pass


class CriterionEvaluationError(MarkingError):
    """Raised when criterion evaluation fails."""
    
    def __init__(self, message: str, task_number: int = None, criterion: str = None):
        super().__init__(message)
        self.task_number = task_number
        self.criterion = criterion
