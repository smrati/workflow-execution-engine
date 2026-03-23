# Workflow Execution Engine

A cron-based workflow execution engine for scheduling and running commands. This daemon-based system reads workflow configurations from a JSON file, executes them according to their cron schedules, and logs all output and metadata to SQLite database.

## Features

- **Cron-based Scheduling**: Use standard cron expressions to define when workflows should run
- **Parallel Execution**: Multiple workflows can run concurrently
- **Persistent Metadata**: All run history stored in SQLite database
- **Detailed Logging**: Each workflow run gets its own timestamped log file
- **Graceful Shutdown**: Handles SIGINT/SIGTERM for clean shutdown

## Installation

```bash
# Clone the repository
cd workflow-execution-engine

# Install dependencies using uv
uv sync
```

## Configuration

Create a `config.json` file in the project root (or specify a custom path):

```json
[
  {
    "name": "hello-world",
    "command": "echo 'Hello from workflow engine!'",
    "cron": "* * * * *",
    "enabled": true
  },
  {
    "name": "python-script",
    "command": "uv run project1/this_1.py",
    "cron": "*/15 * * * *",
    "enabled": true
  },
  {
    "name": "go-program",
    "command": "/path/to/executable my_code.go",
    "cron": "0 * * * *",
    "enabled": true
  }
]
```

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier for the workflow |
| `command` | string | Yes | Shell command to execute |
| `cron` | string | Yes | Cron expression (standard 5-field format) |
| `enabled` | boolean | No | Whether the workflow is active (default: true) |

### Cron Expression Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

Examples:
- `* * * * *` - Every minute
- `*/15 * * * *` - Every 15 minutes
- `0 * * * *` - Every hour
- `0 9 * * 1-5` - 9 AM Monday through Friday

## Usage

### Start the Engine

```bash
# Using uv
uv run python main.py

# With custom options
uv run python main.py --config my-config.json --interval 0.5
```

### Command Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | config.json | Path to configuration file |
| `--db` | `-d` | data/workflows.db | Path to SQLite database |
| `--log-dir` | `-l` | data/logs | Path to log directory |
| `--interval` | `-i` | 1.0 | Check interval in seconds |

### Stop the Engine

Press `Ctrl+C` or send `SIGTERM` to gracefully shutdown the engine. It will wait for running tasks to complete before exiting.

## Project Structure

```
workflow-execution-engine/
├── main.py                 # Entry point
├── config.json             # Workflow definitions
├── pyproject.toml          # Project configuration
├── src/
│   ├── __init__.py
│   ├── engine.py           # Main orchestration logic
│   ├── scheduler.py        # Cron parsing & scheduling
│   ├── executor.py         # Async command execution
│   ├── database.py         # SQLite operations
│   ├── logger.py           # Logging setup
│   └── models.py           # Data models
├── data/
│   ├── workflows.db        # SQLite database (auto-created)
│   └── logs/               # Log files (auto-created)
│       ├── engine.log      # Engine activity log
│       └── {workflow_name}/
│           └── {timestamp}.log
└── README.md
```

## Database Schema

### `workflow_runs` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| workflow_name | TEXT | Name of the workflow |
| command | TEXT | Command that was executed |
| start_time | TEXT | ISO format timestamp |
| end_time | TEXT | ISO format timestamp (nullable) |
| exit_code | INTEGER | Process exit code (nullable) |
| status | TEXT | running, success, or failed |
| log_file_path | TEXT | Path to the log file |

## Querying Run History

You can query the SQLite database directly:

```bash
# Get all runs
sqlite3 data/workflows.db "SELECT * FROM workflow_runs ORDER BY start_time DESC LIMIT 10;"

# Get runs for a specific workflow
sqlite3 data/workflows.db "SELECT * FROM workflow_runs WHERE workflow_name='hello-world';"

# Get failed runs
sqlite3 data/workflows.db "SELECT * FROM workflow_runs WHERE status='failed';"
```

## Log Files

Each workflow run creates a separate log file containing:
- Start timestamp and command
- Real-time stdout and stderr output
- Exit code and completion status
- Duration

Log files are organized by workflow name:
```
data/logs/
├── engine.log           # Engine activity
├── hello-world/
│   ├── 20260323_065800.log
│   └── 20260323_065900.log
└── date-check/
    └── 20260323_070000.log
```

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest
```

### Adding New Workflows

1. Edit `config.json`
2. Add a new workflow object with required fields
3. Restart the engine for changes to take effect

## License

MIT License
</task_progress>
- [x] Create project structure (src/ directory)
- [x] Define data models (models.py)
- [x] Implement SQLite database layer (database.py)
- [x] Implement logging system (logger.py)
- [x] Implement cron scheduler (scheduler.py)
- [x] Implement async command executor (executor.py)
- [x] Implement main engine loop (engine.py)
- [x] Update main.py entry point
- [x] Create sample config.json
- [x] Update pyproject.toml with dependencies
- [ ] Update README.md with usage instructions
- [ ] Test the complete system
</task_progress>
</write_to_file>