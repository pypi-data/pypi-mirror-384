"""
Enums and constants for Schema Onboarding Tracker.

This module contains all the enumerations and constants used throughout
the schema onboarding tracker system.
"""

from enum import Enum


class RunStatus(Enum):
    """Enum for run status values."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskStatus(Enum):
    """Enum for task status values."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ConditionType(Enum):
    """Enum for condition types in template conditions."""
    AND = "AND"
    OR = "OR"


# Constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 30
