import unittest
from abc import ABC

from data_exchange_agent.interfaces.data_source import DataSourceInterface
from data_exchange_agent.interfaces.task_queue import TaskQueueInterface


class TestDataSourceInterface(unittest.TestCase):
    """Test cases for DataSourceInterface abstract base class."""

    def test_data_source_interface_is_abstract(self):
        """Test that DataSourceInterface is an abstract base class."""
        self.assertTrue(issubclass(DataSourceInterface, ABC))

    def test_data_source_interface_cannot_be_instantiated(self):
        """Test that DataSourceInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            DataSourceInterface()

    def test_data_source_interface_has_abstract_methods(self):
        """Test that DataSourceInterface has the expected abstract methods."""
        abstract_methods = DataSourceInterface.__abstractmethods__

        expected_methods = {
            "create_connection",
            "execute_statement",
            "close_connection",
        }

        self.assertEqual(abstract_methods, expected_methods)

    def test_create_connection_is_abstract(self):
        """Test that create_connection is an abstract method."""
        self.assertTrue(hasattr(DataSourceInterface, "create_connection"))
        self.assertTrue(
            getattr(
                DataSourceInterface.create_connection, "__isabstractmethod__", False
            )
        )

    def test_execute_statement_is_abstract(self):
        """Test that execute_statement is an abstract method."""
        self.assertTrue(hasattr(DataSourceInterface, "execute_statement"))
        self.assertTrue(
            getattr(
                DataSourceInterface.execute_statement, "__isabstractmethod__", False
            )
        )

    def test_close_connection_is_abstract(self):
        """Test that close_connection is an abstract method."""
        self.assertTrue(hasattr(DataSourceInterface, "close_connection"))
        self.assertTrue(
            getattr(DataSourceInterface.close_connection, "__isabstractmethod__", False)
        )

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation can be instantiated."""

        class ConcreteDataSource(DataSourceInterface):
            def create_connection(self):
                return "mock_connection"

            def execute_statement(self, statement: str):
                return [{"result": "mock_data"}]

            def close_connection(self):
                pass

        instance = ConcreteDataSource()
        self.assertIsInstance(instance, DataSourceInterface)

    def test_incomplete_implementation_cannot_be_instantiated(self):
        """Test that incomplete implementations cannot be instantiated."""

        class IncompleteDataSource(DataSourceInterface):
            def create_connection(self):
                return "mock_connection"

        with self.assertRaises(TypeError):
            IncompleteDataSource()

    def test_method_signatures(self):
        """Test that abstract methods have correct signatures."""
        import inspect

        create_conn_sig = inspect.signature(DataSourceInterface.create_connection)
        self.assertEqual(len(create_conn_sig.parameters), 1)  # Only 'self'

        exec_stmt_sig = inspect.signature(DataSourceInterface.execute_statement)
        self.assertEqual(
            len(exec_stmt_sig.parameters), 3
        )  # 'self', 'statement', 'results_folder_path'
        params = list(exec_stmt_sig.parameters.keys())
        self.assertEqual(params, ["self", "statement", "results_folder_path"])

        close_conn_sig = inspect.signature(DataSourceInterface.close_connection)
        self.assertEqual(len(close_conn_sig.parameters), 1)  # Only 'self'


class TestTaskQueueInterface(unittest.TestCase):
    """Test cases for TaskQueueInterface abstract base class."""

    def test_task_queue_interface_is_abstract(self):
        """Test that TaskQueueInterface is an abstract base class."""
        self.assertTrue(issubclass(TaskQueueInterface, ABC))

    def test_task_queue_interface_cannot_be_instantiated(self):
        """Test that TaskQueueInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            TaskQueueInterface()

    def test_task_queue_interface_has_abstract_methods(self):
        """Test that TaskQueueInterface has the expected abstract methods."""
        abstract_methods = TaskQueueInterface.__abstractmethods__

        expected_methods = {
            "add_task",
            "get_task",
            "complete_task",
            "fail_task",
            "retry_task",
            "cleanup_stale_tasks",
            "clear_completed_tasks",
            "get_queue_size",
            "get_processing_count",
            "get_completed_count",
            "get_queue_stats",
        }

        self.assertEqual(abstract_methods, expected_methods)

    def test_all_methods_are_abstract(self):
        """Test that all expected methods are abstract."""
        methods_to_check = [
            "add_task",
            "get_task",
            "complete_task",
            "fail_task",
            "retry_task",
            "cleanup_stale_tasks",
            "clear_completed_tasks",
            "get_queue_size",
            "get_processing_count",
            "get_completed_count",
            "get_queue_stats",
        ]

        for method_name in methods_to_check:
            self.assertTrue(hasattr(TaskQueueInterface, method_name))
            method = getattr(TaskQueueInterface, method_name)
            self.assertTrue(getattr(method, "__isabstractmethod__", False))

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation can be instantiated."""

        class ConcreteTaskQueue(TaskQueueInterface):
            def add_task(self, task: dict[str, any]) -> None:
                pass

            def get_task(self, worker_id: str | None = None) -> dict[str, any] | None:
                return None

            def complete_task(self, task: dict[str, any]) -> None:
                pass

            def fail_task(
                self, task: dict[str, any], error_message: str = None
            ) -> None:
                pass

            def retry_task(self, task: dict[str, any]) -> None:
                pass

            def cleanup_stale_tasks(self, timeout_seconds: int = 300) -> int:
                return 0

            def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
                return 0

            def get_queue_size(self) -> int:
                return 0

            def get_processing_count(self) -> int:
                return 0

            def get_completed_count(self) -> int:
                return 0

            def get_queue_stats(self) -> dict[str, int]:
                return {}

        instance = ConcreteTaskQueue()
        self.assertIsInstance(instance, TaskQueueInterface)

    def test_incomplete_implementation_cannot_be_instantiated(self):
        """Test that incomplete implementations cannot be instantiated."""

        class IncompleteTaskQueue(TaskQueueInterface):
            def add_task(self, task: dict[str, any]) -> None:
                pass

            def get_task(self, worker_id: str | None = None) -> dict[str, any] | None:
                return None

        with self.assertRaises(TypeError):
            IncompleteTaskQueue()

    def test_method_signatures(self):
        """Test that abstract methods have correct signatures."""
        import inspect

        add_task_sig = inspect.signature(TaskQueueInterface.add_task)
        params = list(add_task_sig.parameters.keys())
        self.assertEqual(params, ["self", "task"])

        get_task_sig = inspect.signature(TaskQueueInterface.get_task)
        params = list(get_task_sig.parameters.keys())
        self.assertEqual(params, ["self", "worker_id"])

        fail_task_sig = inspect.signature(TaskQueueInterface.fail_task)
        params = list(fail_task_sig.parameters.keys())
        self.assertEqual(params, ["self", "task", "error_message"])

        cleanup_sig = inspect.signature(TaskQueueInterface.cleanup_stale_tasks)
        params = list(cleanup_sig.parameters.keys())
        self.assertEqual(params, ["self", "timeout_seconds"])

        clear_sig = inspect.signature(TaskQueueInterface.clear_completed_tasks)
        params = list(clear_sig.parameters.keys())
        self.assertEqual(params, ["self", "older_than_hours"])

    def test_method_return_types(self):
        """Test that methods have correct return type annotations."""
        import inspect

        int_methods = [
            "cleanup_stale_tasks",
            "clear_completed_tasks",
            "get_queue_size",
            "get_processing_count",
            "get_completed_count",
        ]

        for method_name in int_methods:
            method = getattr(TaskQueueInterface, method_name)
            sig = inspect.signature(method)
            self.assertEqual(sig.return_annotation, int)

        stats_method = getattr(TaskQueueInterface, "get_queue_stats")
        stats_sig = inspect.signature(stats_method)
        self.assertEqual(stats_sig.return_annotation, dict[str, int])

        none_methods = ["add_task", "complete_task", "fail_task", "retry_task"]

        for method_name in none_methods:
            method = getattr(TaskQueueInterface, method_name)
            sig = inspect.signature(method)
            self.assertEqual(sig.return_annotation, None)


if __name__ == "__main__":
    unittest.main()
