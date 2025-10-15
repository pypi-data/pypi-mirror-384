"""Task status enumeration definitions."""

from enum import Enum


class TaskStatus(Enum):
    """
    Enum representing possible task statuses.

    Used to track the state of data extraction tasks throughout their lifecycle.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    COMPLETED = "completed"
