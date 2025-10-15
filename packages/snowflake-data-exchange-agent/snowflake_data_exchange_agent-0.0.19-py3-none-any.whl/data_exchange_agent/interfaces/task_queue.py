"""
Task queue interface definition.

This module defines the abstract base class interface that all task queue
implementations must follow for managing and processing tasks.
"""

from abc import ABC, abstractmethod


class TaskQueueInterface(ABC):
    """
    Abstract base class for task queue implementations.

    This interface defines the contract that all task queue implementations
    must follow for adding, retrieving, and managing tasks in the system.
    """

    @abstractmethod
    def add_task(self, task: dict[str, any]) -> None:
        """
        Add a new task to the queue.

        Args:
            task: Dictionary containing task data and metadata

        """
        pass

    @abstractmethod
    def get_task(self, worker_id: str | None = None) -> dict[str, any] | None:
        """
        Retrieve the next available task from the queue.

        Args:
            worker_id: Optional worker identifier for task assignment

        Returns:
            Task dictionary if available, None if queue is empty

        """
        pass

    @abstractmethod
    def complete_task(self, task: dict[str, any]) -> None:
        """
        Mark a task as completed and remove it from active processing.

        Args:
            task: Dictionary containing the completed task data

        """
        pass

    @abstractmethod
    def fail_task(self, task: dict[str, any], error_message: str = None) -> None:
        """
        Mark task as failed.

        Args:
            task: Dictionary containing the failed task data
            error_message: Optional error message describing the failure

        """
        pass

    @abstractmethod
    def retry_task(self, task: dict[str, any]) -> None:
        """
        Move failed task back to pending for retry.

        Args:
            task: Dictionary containing the task to retry

        """
        pass

    @abstractmethod
    def cleanup_stale_tasks(self, timeout_seconds: int = 300) -> int:
        """
        Move stale processing tasks back to pending (worker died).

        Args:
            timeout_seconds: Time after which processing tasks are considered stale

        Returns:
            Number of stale tasks that were cleaned up

        """
        pass

    @abstractmethod
    def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Remove old completed tasks to keep database size manageable.

        Args:
            older_than_hours: Remove completed tasks older than this many hours

        Returns:
            Number of tasks that were removed

        """
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """
        Get the number of pending tasks in the queue.

        Returns:
            Number of pending tasks

        """
        pass

    @abstractmethod
    def get_processing_count(self) -> int:
        """
        Get the number of tasks currently being processed.

        Returns:
            Number of tasks being processed

        """
        pass

    @abstractmethod
    def get_completed_count(self) -> int:
        """
        Get the number of completed tasks.

        Returns:
            Number of completed tasks

        """
        pass

    @abstractmethod
    def get_queue_stats(self) -> dict[str, int]:
        """
        Get comprehensive statistics about the task queue.

        Returns:
            Dictionary containing queue statistics (pending, processing, completed, failed, etc.)

        """
        pass
