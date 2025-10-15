"""
SQLite-based persistent task queue implementation.

This module provides the SQLiteTaskQueue class which implements a persistent
task queue using SQLite database. It provides durability, concurrent access
control, and advanced task management features like retry logic and cleanup.
"""

import json
import os
import sqlite3
import threading

from contextlib import contextmanager

from data_exchange_agent.constants.paths import DB_TASKS_FILE_PATH
from data_exchange_agent.constants.task import TOTAL
from data_exchange_agent.enums.task_status import TaskStatus
from data_exchange_agent.interfaces.task_queue import TaskQueueInterface


class SQLiteTaskQueue(TaskQueueInterface):
    """Thread-safe SQLite-based task queue - perfect for multi-worker setup."""

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize the SQLite task queue.

        Sets up the SQLite database connection, creates necessary directories,
        initializes the database schema, and configures thread-local storage
        for safe concurrent access across multiple worker threads.

        Args:
            db_path (str | None): Path to the SQLite database file. If None,
                                 uses the default path from configuration.

        """
        if db_path is None:
            db_path = DB_TASKS_FILE_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._local = threading.local()  # Thread-local storage for connections
        self._init_db()

        print(f"SQLite Task Queue initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout for locks
                isolation_level=None,  # Autocommit mode for better concurrency
            )

            # Enable WAL mode for better concurrent access
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys if needed
            self._local.connection.execute("PRAGMA foreign_keys=ON")
            # Optimize for our use case
            self._local.connection.execute("PRAGMA synchronous=NORMAL")

        return self._local.connection

    @contextmanager
    def _get_cursor(self):
        """Context manager for database operations."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _init_db(self):
        """Initialize database schema."""
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as _:
                pass

        with self._get_cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    task_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT '{TaskStatus.PENDING.value}',
                    worker_pid INTEGER,
                    worker_thread TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                )
            """
            )

            cursor.execute(
                """CREATE TABLE IF NOT EXISTS task_status(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """
            )

            # Check if task_status table exists and add states if needed
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='task_status'
            """
            )

            if cursor.fetchone():
                # Add task states if table exists
                states = [
                    TaskStatus.PENDING.value,
                    TaskStatus.PROCESSING.value,
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                ]
                cursor.executemany(
                    "INSERT OR IGNORE INTO task_status (name) VALUES (?)",
                    [(state,) for state in states],
                )

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_worker ON tasks(worker_pid, worker_thread)"
            )

    def add_task(self, task: dict[str, any]) -> None:
        """Add task to queue - thread-safe."""
        task_id = str(task.get("id"))
        task_data = json.dumps(task)

        with self._get_cursor() as cursor:
            try:
                cursor.execute(
                    f"""
                    INSERT INTO tasks (task_id, task_data, status)
                    VALUES (?, ?, '{TaskStatus.PENDING.value}')
                """,
                    (task_id, task_data),
                )

                print(f"Task {task_id} added to SQLite queue")

            except sqlite3.IntegrityError:
                # Task already exists, update it
                cursor.execute(
                    f"""
                    UPDATE tasks
                    SET task_data = ?, status = '{TaskStatus.PENDING.value}',
                        started_at = NULL, completed_at = NULL,
                        worker_pid = NULL, worker_thread = NULL,
                        error_message = NULL
                    WHERE task_id = ?
                """,
                    (task_data, task_id),
                )

                print(f"Task {task_id} updated in SQLite queue")

    def get_task(self, worker_id: str | None = None) -> dict[str, any] | None:
        """Get and claim next pending task - atomic operation."""
        if worker_id is None:
            worker_id = f"{os.getpid()}_{threading.current_thread().ident}"

        with self._get_cursor() as cursor:
            try:
                # Atomic: get oldest pending task and mark as processing
                cursor.execute(
                    f"""
                    UPDATE tasks
                    SET status = '{TaskStatus.PROCESSING.value}',
                        worker_pid = ?,
                        worker_thread = ?,
                        started_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id FROM tasks
                        WHERE status = '{TaskStatus.PENDING.value}'
                        ORDER BY created_at ASC
                        LIMIT 1
                    )
                    RETURNING task_id, task_data, id
                """,
                    (os.getpid(), worker_id),
                )

                row = cursor.fetchone()
                if row:
                    task_id, task_data, db_id = row
                    task = json.loads(task_data)
                    task["_db_id"] = db_id  # For completion tracking
                    task["_worker_id"] = worker_id

                    print(f"Worker {worker_id} claimed task: {task_id}")
                    return task

            except sqlite3.OperationalError as e:
                print(f"Database error in get_task: {e}")
                # Database might be locked, return None and retry later

        return None

    def complete_task(self, task: dict[str, any]) -> None:
        """Mark task as completed."""
        task_id = str(task.get("id"))

        with self._get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = NULL
                WHERE task_id = ? AND status = 'processing'
            """,
                (task_id,),
            )

            if cursor.rowcount > 0:
                print(f"Task {task_id} marked as completed")
            else:
                print(f"Warning: Task {task_id} was not in processing state")

    def fail_task(self, task: dict[str, any], error_message: str = None) -> None:
        """Mark task as failed."""
        task_id = str(task.get("id"))

        with self._get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET status = 'failed',
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = ?
                WHERE task_id = ? AND status = 'processing'
            """,
                (error_message, task_id),
            )

            print(f"Task {task_id} marked as failed: {error_message}")

    def retry_task(self, task: dict[str, any]) -> None:
        """Move failed task back to pending for retry."""
        task_id = str(task.get("id"))

        with self._get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tasks
                SET status = '{TaskStatus.PENDING.value}',
                    worker_pid = NULL,
                    worker_thread = NULL,
                    started_at = NULL,
                    completed_at = NULL,
                    error_message = NULL
                WHERE task_id = ?
            """,
                (task_id,),
            )

            print(f"Task {task_id} moved back to pending for retry")

    def get_queue_size(self) -> int:
        """Get number of pending tasks."""
        with self._get_cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks WHERE status = '{TaskStatus.PENDING.value}'"
            )
            return cursor.fetchone()[0]

    def get_processing_count(self) -> int:
        """Get number of tasks currently being processed."""
        with self._get_cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks WHERE status = '{TaskStatus.PROCESSING.value}'"
            )
            return cursor.fetchone()[0]

    def get_completed_count(self) -> int:
        """Get number of completed tasks."""
        with self._get_cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM tasks WHERE status = '{TaskStatus.COMPLETED.value}'"
            )
            return cursor.fetchone()[0]

    def get_queue_stats(self) -> dict[str, int]:
        """Get comprehensive queue statistics."""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    status,
                    COUNT(*) as count
                FROM tasks
                GROUP BY status
            """
            )

            stats = {}
            for status, count in cursor.fetchall():
                stats[status] = count

            return {
                TaskStatus.PENDING.value: stats.get(TaskStatus.PENDING.value, 0),
                TaskStatus.PROCESSING.value: stats.get(TaskStatus.PROCESSING.value, 0),
                TaskStatus.COMPLETED.value: stats.get(TaskStatus.COMPLETED.value, 0),
                TaskStatus.FAILED.value: stats.get(TaskStatus.FAILED.value, 0),
                TOTAL: sum(stats.values()),
            }

    def cleanup_stale_tasks(self, timeout_seconds: int = 300) -> int:
        """Move stale processing tasks back to pending (worker died)."""
        with self._get_cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE tasks
                SET status = '{TaskStatus.PENDING.value}',
                    worker_pid = NULL,
                    worker_thread = NULL,
                    started_at = NULL
                WHERE status = '{TaskStatus.PROCESSING.value}'
                    AND started_at < datetime('now', '-{timeout_seconds} seconds')
            """
            )

            stale_count = cursor.rowcount
            if stale_count > 0:
                print(f"Cleaned up {stale_count} stale tasks")

            return stale_count

    def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Remove old completed tasks to keep database size manageable."""
        with self._get_cursor() as cursor:
            cursor.execute(
                f"""
                DELETE FROM tasks
                WHERE status IN ('{TaskStatus.COMPLETED.value}', '{TaskStatus.FAILED.value}')
                    AND completed_at < datetime('now', '-{older_than_hours} hours')
            """
            )

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"Deleted {deleted_count} old completed tasks")

            return deleted_count

    def close(self):
        """Close the database connection to allow file cleanup."""
        # We only want to close the connection for the current thread
        if hasattr(self._local, "connection"):
            try:
                self._local.connection.close()
                delattr(self._local, "connection")
            except Exception:
                # Ignore errors during cleanup
                pass
