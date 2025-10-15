# Data Exchange Agent - Test Suite

This directory contains comprehensive tests for all modules in the `data_exchange_agent` package.

## Test Structure

The test suite is organized to mirror the source code structure and provides comprehensive coverage for all components:

### Core Module Tests
- `test_config.py` - Tests for configuration management
- `test_container.py` - Tests for dependency injection container
- `test_main.py` - Tests for main application entry point

### API and Task Management Tests
- `test_api_manager.py` - Tests for API communication manager
- `test_task_manager.py` - Tests for task processing and management
- `test_flask_app.py` - Tests for Flask web server implementation
- `test_waitress_app.py` - Tests for Waitress production server

### Queue Implementation Tests
- `test_sqlite_task_queue.py` - Tests for SQLite-based task queue
- `test_deque_task_queue.py` - Tests for in-memory deque task queue

### Data Source Tests
- `test_extractor.py` - Tests for data extraction wrapper (existing)
- `test_data_sources_interfaces.py` - Tests for abstract interfaces
- `test_pyspark_data_source.py` - Tests for PySpark data source implementation
- `test_sqlalchemy_data_source.py` - Tests for SQLAlchemy data source implementation

### JDBC Management Tests
- `test_jdbc_jar.py` - Tests for JDBC JAR file management
- `test_jdbc_jar_dict.py` - Tests for JDBC JAR dictionary manager

### Utility Tests
- `test_utils_decorators.py` - Tests for decorator functions
- `test_utils_sf_logger.py` - Tests for custom logging implementation
- `test_utils_constants.py` - Tests for application constants
- `test_utils_utils.py` - Tests for utility functions

### Integration Tests
- `test_integration.py` - Integration tests for component interactions

## Test Features

### Comprehensive Coverage
- **Unit Tests**: Individual component testing with mocking
- **Integration Tests**: Component interaction testing
- **Error Handling**: Exception and edge case testing
- **Concurrency Testing**: Thread safety and concurrent operations
- **Configuration Testing**: Various configuration scenarios

### Test Utilities
- `test_runner.py` - Comprehensive test runner with detailed reporting
- Mock implementations for external dependencies
- Temporary file and database management for isolated testing

## Running Tests

### Run All Tests
```bash
# Using the test runner
python tests/test_runner.py

# Using unittest discovery
python -m unittest discover tests/

# Using pytest (if installed)
pytest tests/
```

### Run Specific Test Files
```bash
# Run a specific test file
python -m unittest tests.test_config

# Run a specific test class
python -m unittest tests.test_config.TestConfig

# Run a specific test method
python -m unittest tests.test_config.TestConfig.test_config_default_values
```

### Run Tests with Coverage
```bash
# Install coverage if not already installed
pip install coverage

# Run tests with coverage
coverage run -m unittest discover tests/
coverage report
coverage html  # Generate HTML coverage report
```

## Test Categories

### 1. Unit Tests
Each module has comprehensive unit tests covering:
- Initialization and configuration
- Method functionality
- Error handling and edge cases
- Property getters and setters
- Type validation

### 2. Integration Tests
Integration tests verify:
- Component interactions
- Data flow between modules
- End-to-end functionality
- Concurrent operations
- Database operations

### 3. Mock Testing
Extensive use of mocking for:
- External API calls
- Database connections
- File system operations
- Network operations
- Threading and concurrency

## Test Patterns

### Common Patterns Used
1. **Setup/Teardown**: Proper test isolation with setUp() and tearDown()
2. **Mocking**: Comprehensive mocking of external dependencies
3. **Parameterized Tests**: Using subTest() for multiple test cases
4. **Exception Testing**: Proper exception handling verification
5. **Thread Safety**: Concurrent operation testing

### Mock Strategies
- **Patch Decorators**: For method-level mocking
- **Context Managers**: For temporary mocking
- **Mock Objects**: For complex object simulation
- **Side Effects**: For exception and complex behavior simulation

## Dependencies

The test suite requires:
- `unittest` (built-in)
- `unittest.mock` (built-in)
- All production dependencies (for integration tests)

Optional dependencies for enhanced testing:
- `coverage` - For test coverage analysis
- `pytest` - Alternative test runner
- `pytest-cov` - Coverage plugin for pytest

## Best Practices

### Test Organization
- One test file per source module
- Descriptive test method names
- Logical grouping of related tests
- Clear test documentation

### Test Quality
- High test coverage (aim for >90%)
- Fast test execution
- Isolated test cases
- Deterministic test results
- Clear assertion messages

### Maintenance
- Regular test updates with code changes
- Removal of obsolete tests
- Performance optimization for slow tests
- Documentation updates

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure PYTHONPATH includes src directory
2. **Database Locks**: Use temporary databases for SQLite tests
3. **Threading Issues**: Proper cleanup of threads and locks
4. **Mock Conflicts**: Reset mocks between tests

### Debug Tips
- Use `python -m unittest -v` for verbose output
- Add print statements for debugging (remove before commit)
- Use `pdb` for interactive debugging
- Check test isolation by running tests in different orders

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Include comprehensive docstrings
3. Test both success and failure cases
4. Mock external dependencies
5. Ensure test isolation
6. Update this README if needed

## Test Metrics

The test suite includes:
- **20+ test files** covering all modules
- **200+ individual test methods**
- **Comprehensive mocking** of external dependencies
- **Integration tests** for component interactions
- **Concurrent testing** for thread safety
- **Error handling** for edge cases
