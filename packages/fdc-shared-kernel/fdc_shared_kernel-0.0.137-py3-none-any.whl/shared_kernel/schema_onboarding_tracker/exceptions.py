"""
Custom exceptions for Schema Onboarding Tracker.

This module contains all custom exceptions used throughout
the schema onboarding tracker system.
"""

from shared_kernel.exceptions.custom_exceptions import BaseCustomException


class SchemaOnboardingTrackerException(BaseCustomException):
    """Base exception for schema onboarding tracker operations."""
    
    def __init__(self, message: str = "An error occurred in schema onboarding tracker.", details: str = "") -> None:
        super().__init__(message=message, details=details)


class TemplateNotFoundException(SchemaOnboardingTrackerException):
    """Raised when a template is not found."""
    
    def __init__(self, template_name: str) -> None:
        super().__init__(f"Template '{template_name}' not found")


class RunNotFoundException(SchemaOnboardingTrackerException):
    """Raised when a run is not found."""
    
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Run '{run_id}' not found")


class TaskNotFoundException(SchemaOnboardingTrackerException):
    """Raised when a task is not found."""
    
    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task '{task_id}' not found")


class InvalidTemplateDataException(SchemaOnboardingTrackerException):
    """Raised when template data is invalid."""
    
    def __init__(self, message: str = "Invalid template data provided") -> None:
        super().__init__(message)


class InvalidRunDataException(SchemaOnboardingTrackerException):
    """Raised when run data is invalid."""
    
    def __init__(self, message: str = "Invalid run data provided") -> None:
        super().__init__(message)


class InvalidTaskDataException(SchemaOnboardingTrackerException):
    """Raised when task data is invalid."""
    
    def __init__(self, message: str = "Invalid task data provided") -> None:
        super().__init__(message)
