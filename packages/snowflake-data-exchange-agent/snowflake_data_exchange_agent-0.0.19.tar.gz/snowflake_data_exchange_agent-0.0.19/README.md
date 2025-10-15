# Snowflake Data Exchange Agent

[![License Apache-2.0](https://img.shields.io/:license-Apache%202-brightgreen.svg)](http://www.apache.org/licenses/LICENSE-2.0.txt)
[![Python](https://img.shields.io/badge/python-3.10--3.12-blue)](https://www.python.org/downloads/)

A REST API service for database migrations and data validation. Supports multiple databases including Snowflake, PostgreSQL, and SQL Server with queue-based task processing.

## Quick Start

```bash
# Install
pip install snowflake-data-exchange-agent

# Run
data-exchange-agent --port 8080

# Test
curl http://localhost:8080/health
```

## Installation

### From PyPI (Production)
```bash
pip install snowflake-data-exchange-agent
```

### Requirements & Dependencies

**Python Version**: 3.10, 3.11, or 3.12 (3.13 not yet supported)

**Available dependency groups**:
- `development`: Testing and development tools (pytest, ruff, etc.)
- `all`: Includes all development dependencies

**Core dependencies include**:
- Snowflake Connector for Python
- PySpark for data processing
- Flask + Waitress for REST API
- PostgreSQL support (psycopg2-binary)
- AWS SDK (boto3)

## Configuration

Create `src/data_exchange_agent/configuration.toml`:

```toml
# API settings
[api_configuration]
key = "your-api-key"
host = "0.0.0.0"
port = 5001
workers = 4

# Database connections
[connection.postgresql]
driver_name = "postgresql"
username = "user"
password = "password"
host = "localhost"
port = 5432
database = "mydb"

# Task queue
[task_queue]
type = "sqlite"
database_path = "~/.data_exchange_agent/tasks.db"
```

For Snowflake, create `~/.snowflake/config.toml`:

```toml
[connections.default]
account = "your_account.region"
user = "your_username"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "PRODUCTION_DB"
```

## API Usage

### Command Line
```bash
# Basic usage
data-exchange-agent

# Production settings
data-exchange-agent --workers 8 --port 8080

# Debug mode
data-exchange-agent --debug --port 5001
```

### Health Check
```http
GET /health
```
```json
{
  "status": "healthy",
  "version": "0.0.18",
  "database_connections": {
    "snowflake": "connected"
  }
}
```

### Task Management
```http
# Start processing
GET /handle_tasks

# Stop processing
GET /stop

# Get status
GET /get_handling_tasks_status

# Task count
GET /get_tasks_count
```

### Add Task
```http
POST /tasks
Content-Type: application/json
```
```json
{
  "task_type": "data_extraction",
  "source_config": {
    "database": "postgresql",
    "query": "SELECT * FROM users"
  },
  "destination_config": {
    "type": "snowflake_stage",
    "stage": "@data_stage/users/"
  }
}
```

## Development

### Setup
```bash
git clone https://github.com/snowflakedb/migrations-data-validation.git
cd migrations-data-validation/data-exchange-agent
pip install -e .[development]
```

### Testing
```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/data_exchange_agent

# Run specific test types
pytest tests/unit/           # Unit tests only
pytest -m "not integration" # Non-integration tests
```

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](../CONTRIBUTING.md) for details on how to collaborate, set up your development environment, and submit PRs.

---

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full documentation](https://github.com/snowflakedb/migrations-data-validation)
- **Issues**: [GitHub Issues](https://github.com/snowflakedb/migrations-data-validation/issues)

---

**Developed with ❄️ by Snowflake**
