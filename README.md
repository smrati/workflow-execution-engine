# Workflow Execution Engine

A production-ready cron-based workflow execution engine with a modern web UI for monitoring, management, and observability. Schedule any shell command to run on a cron schedule, monitor executions in real time, and manage access with role-based user accounts.

## What Is This?

This is a self-hosted alternative to tools like Airflow (for simple use cases), GitHub Actions cron jobs, or systemd timers -- but with a built-in web dashboard, REST API, authentication, and detailed run history.

### Use Cases

- **Scheduled system maintenance**: Run disk cleanup, log rotation, backups on cron schedules
- **Monitoring and health checks**: Periodically run health check scripts and track results
- **Data pipeline orchestration**: Schedule ETL jobs, data imports, report generation
- **DevOps automation**: Run deployment scripts, certificate renewal, database vacuuming
- **Team observability**: Give team members read-only access to monitor workflow health

### Key Features

- **Cron-based scheduling** with standard 5-field cron expressions
- **Parallel execution** with configurable concurrency limit (default: 10)
- **Automatic retries** with configurable count and delay
- **Command timeout** support per workflow
- **Persistent run history** stored in SQLite or PostgreSQL
- **Per-run log files** with timestamped output capture
- **Real-time WebSocket updates** for live status changes
- **JWT authentication** with role-based access control (admin, normal, viewer)
- **Run log cleanup** with before/after/between date range filters
- **Timezone-aware UI** with selectable timezone (persisted per user)
- **Trigger tracking** -- know whether a run was triggered by cron or by a specific user
- **REST API** with OpenAPI docs at `/docs`
- **Graceful shutdown** -- waits for running tasks before exiting

---

## Architecture

The system has two components:

```
+--------------------+         +-----------------------+
|   Frontend UI     |  HTTP   |    Backend Server     |
|  React + Vite     |<------->|  FastAPI + Engine     |
|  localhost:5173   |   WS    |  localhost:8000       |
+--------------------+         +-----------+-----------+
                                          |
                              +-----------+-----------+
                              |  config.json           |
                              |  data/workflows.db    |
                              |  data/logs/            |
                              +-----------------------+
```

| Component | Description |
|-----------|-------------|
| **Backend** | FastAPI server + cron engine + WebSocket + SQLite (single process) |
| **Frontend** | React SPA with Tailwind CSS, runs independently |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- PostgreSQL (optional, for production database)

### 1. Clone and Install

```bash
git clone <repository-url>
cd workflow-execution-engine

uv sync
cd frontend && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example.sh .env.sh
# Edit .env.sh and set JWT_SECRET_KEY (generate with: openssl rand -hex 32)
source .env.sh
```

### 3. Configure Workflows

```bash
cp config.example.json config.json
# Edit config.json to define your workflows
```

### 4. Start Backend

```bash
uv run python run_combined.py
```

### 5. Start Frontend (separate terminal)

```bash
cd frontend && npm run dev
```

### 6. Access

| Service | URL |
|---------|-----|
| Web UI | http://localhost:5173 |
| API Server | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### First-Time Setup

1. Open http://localhost:5173
2. Register the first user -- this account automatically becomes **admin**
3. Subsequent self-registration is disabled
4. Use the **User Management** page (admin only) to create additional users

---

## User Roles and Permissions

| Role | View Workflows/Runs | Trigger/Enable/Disable | Manage Users | Delete Runs |
|------|:-------------------:|:---------------------:|:------------:|:-----------:|
| **admin** | Yes | Yes | Yes | Yes |
| **normal** | Yes | Yes | No | No |
| **viewer** | Yes | No | No | No |

### Token Lifecycle

| Token | Lifetime | Purpose |
|-------|----------|---------|
| Access Token | 15 minutes | Authenticate API requests |
| Refresh Token | 7 days | Obtain new access tokens |

---

## Configuration

Workflows are defined in `config.json` as a JSON array:

```json
[
  {
    "name": "hello-world",
    "command": "echo 'Hello from workflow engine!'",
    "cron": "* * * * *",
    "enabled": true,
    "timeout": 60,
    "retry_count": 3,
    "retry_delay": 30,
    "working_dir": "/home/user/projects",
    "env": { "NODE_ENV": "production" }
  }
]
```

### Workflow Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | -- | Unique identifier |
| `command` | string | Yes | -- | Shell command to execute |
| `cron` | string | Yes | -- | 5-field cron expression |
| `enabled` | boolean | No | `true` | Whether the workflow is active |
| `timeout` | integer | No | `none` | Max execution time in seconds |
| `retry_count` | integer | No | `0` | Number of retries on failure |
| `retry_delay` | integer | No | `60` | Seconds between retries |
| `working_dir` | string | No | current | Working directory for the command |
| `env` | object | No | `{}` | Environment variables for the command |

### Cron Expression Reference

```
+----------------- minute (0 - 59)
| +--------------- hour (0 - 23)
| | +------------- day of month (1 - 31)
| | | +----------- month (1 - 12)
| | | | +--------- day of week (0 - 6, Sun-Sat)
* * * * *
```

| Expression | Description |
|-----------|-------------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `*/30 * * * *` | Every 30 minutes |
| `0 9 * * 1-5` | 9 AM, Monday to Friday |
| `0 0 1 * *` | Midnight on the 1st of every month |

---

## Web UI Features

### Dashboard
- Status cards: total workflows, enabled workflows, total runs, success rate, running tasks
- Activity feed: recent workflow executions with live updates via WebSocket

### Workflows
- Table and card views of all configured workflows
- Run Now button, Enable/Disable toggles
- Next scheduled run time (displayed in user-selected timezone)

### Run History
- Paginated table with all workflow executions
- Filter by workflow name and status (running, success, failed, timeout, retry)
- **Triggered By** column: shows `cron` for scheduled runs or the username for manual triggers
- **Cleanup Runs** button (admin only): delete runs by date range with confirmation dialog

### Run Detail
- Full run metadata: command, start/end time, duration, exit code, attempt number, triggered by
- Log viewer with full stdout/stderr output

### User Management (Admin Only)
- Create users with role selection (admin, normal, viewer)
- Change roles, delete users
- Role badges with color coding

### Timezone Selector
- Dropdown in the header with 12 major timezones
- Selection persists across sessions (stored in localStorage)
- All timestamps in the UI respect the selected timezone

---

## API Reference

### Authentication

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/auth/register` | Public (first user only) | Register admin account |
| POST | `/api/auth/login` | Public | Login, get access + refresh tokens |
| POST | `/api/auth/refresh` | Public | Refresh access token |
| GET | `/api/auth/me` | Authenticated | Get current user info |

### User Management (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/users` | Create a new user |
| GET | `/api/auth/users` | List all users |
| PUT | `/api/auth/users/{id}/role` | Update a user's role |
| DELETE | `/api/auth/users/{id}` | Delete a user |

### Workflows

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/workflows` | All authenticated | List all workflows |
| GET | `/api/workflows/{name}` | All authenticated | Workflow details with stats |
| GET | `/api/workflows/{name}/schedule` | All authenticated | Schedule information |
| POST | `/api/workflows/{name}/run` | Admin, Normal | Trigger a manual run |
| PUT | `/api/workflows/{name}/enable` | Admin, Normal | Enable a workflow |
| PUT | `/api/workflows/{name}/disable` | Admin, Normal | Disable a workflow |

### Runs

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/runs` | All authenticated | List runs (paginated, filterable) |
| GET | `/api/runs/{id}` | All authenticated | Get specific run details |
| DELETE | `/api/runs/cleanup` | Admin | Delete runs by date range |

**Cleanup request body:**
```json
{
  "before": "2026-01-01T00:00:00",
  "after": "2025-01-01T00:00:00",
  "workflow_name": "hello-world"
}
```
Provide `before` and/or `after` in ISO format. `workflow_name` is optional.

### Stats and Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats/engine` | Engine status (running, concurrent tasks, uptime) |
| GET | `/api/stats/overview` | Dashboard summary with recent runs |
| GET | `/api/stats/workflows/{name}` | Per-workflow success/fail stats |
| GET | `/api/logs/{run_id}` | Log file content for a specific run |

### WebSocket

Connect to `ws://localhost:8000/ws` for real-time event broadcasts:

| Event | Description |
|-------|-------------|
| `run_started` | A workflow execution has started |
| `run_completed` | A workflow execution has finished |
| `workflow_event` | Workflow added, removed, enabled, or disabled |
| `stats_update` | Dashboard statistics changed |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes | `your-secret-key-change-in-production` | Secret key for signing JWT tokens |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///data/workflows.db` | SQLAlchemy database URL (SQLite or PostgreSQL) |

Set via `.env.sh` (see `.env.example.sh` for template):
```bash
cp .env.example.sh .env.sh
# Edit and source before every run:
source .env.sh
```

---

## Database

The engine uses SQLAlchemy Core, supporting **SQLite** (default) and **PostgreSQL**. Switch databases by setting the `DATABASE_URL` environment variable -- no code changes needed.

### SQLite (Default)

Zero configuration -- works out of the box. Best for single-instance deployments, development, and small workloads.

```bash
# Default -- nothing to configure
uv run python run_combined.py
```

Database file: `data/workflows.db` (auto-created).

### PostgreSQL

For production, multi-instance deployments, or high-concurrency workloads.

```bash
# Set via environment variable
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/workflow_engine uv run python run_combined.py

# Or via CLI flag
uv run python run_combined.py --database-url "postgresql+asyncpg://user:pass@localhost:5432/workflow_engine"
```

**Setting up PostgreSQL:**

```bash
# Create database
createdb workflow_engine

# Or via Docker
docker run -d \
  --name workflow-pg \
  -e POSTGRES_DB=workflow_engine \
  -e POSTGRES_USER=workflow \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  postgres:16-alpine
```

Then start the engine:
```bash
DATABASE_URL=postgresql+asyncpg://workflow:yourpassword@localhost:5432/workflow_engine \
  uv run python run_combined.py
```

### Database URL Format

| Database | URL Format |
|----------|-----------|
| SQLite (default) | `sqlite+aiosqlite:///data/workflows.db` |
| PostgreSQL | `postgresql+asyncpg://user:pass@host:5432/dbname` |

### Environment Variable

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///data/workflows.db` | SQLAlchemy database URL |

### Schema

**`users` table:**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | User ID |
| username | TEXT UNIQUE | Username |
| hashed_password | TEXT | Bcrypt hash |
| role | TEXT | `admin`, `normal`, or `viewer` |
| created_at | TEXT | ISO timestamp |

**`workflow_runs` table:**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Run ID |
| workflow_name | TEXT | Workflow name |
| command | TEXT | Executed command |
| start_time | TEXT | ISO timestamp |
| end_time | TEXT | ISO timestamp (nullable) |
| exit_code | INTEGER | Process exit code (nullable) |
| status | TEXT | `running`, `success`, `failed`, `timeout` |
| log_file_path | TEXT | Path to log file |
| attempt | INTEGER | Retry attempt number (1 = first) |
| triggered_by | TEXT | Username if manual, NULL if cron |

### Direct Queries

```bash
# Recent runs
sqlite3 data/workflows.db "SELECT * FROM workflow_runs ORDER BY start_time DESC LIMIT 10;"

# Failed runs
sqlite3 data/workflows.db "SELECT * FROM workflow_runs WHERE status='failed';"

# Manual runs by a specific user
sqlite3 data/workflows.db "SELECT * FROM workflow_runs WHERE triggered_by='alice';"

# Cron-only runs
sqlite3 data/workflows.db "SELECT * FROM workflow_runs WHERE triggered_by IS NULL;"
```

---

## Log Files

Each run produces a timestamped log file under `data/logs/<workflow_name>/`:

```
data/logs/
+-- engine.log
+-- hello-world/
|   +-- 20260326_040000.log
|   +-- 20260326_040100.log
+-- disk-usage/
    +-- 20260326_050000.log
```

---

## Running Options

| Command | Description |
|---------|-------------|
| `uv run python run_combined.py` | Engine + API server (recommended) |
| `uv run python main.py` | Engine only (no web UI) |
| `uv run python run_api.py` | API server only (no engine) |
| `uv run python cli.py status` | CLI: show engine status |
| `uv run python cli.py history` | CLI: show run history |
| `uv run python cli.py history -w <name>` | CLI: filter history by workflow |
| `uv run python cli.py logs <run_id>` | CLI: show logs for a run |
| `uv run python cli.py stats <name>` | CLI: workflow statistics |
| `uv run python cli.py cleanup --days 30` | CLI: delete runs older than N days |

### CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | `config.json` | Path to workflow config file |
| `--db` | `-d` | `data/workflows.db` | SQLite database path |
| `--log-dir` | `-l` | `data/logs` | Log directory path |
| `--interval` | `-i` | `1.0` | Scheduler check interval (seconds) |

---

## Project Structure

```
workflow-execution-engine/
+-- run_combined.py              # Engine + API (main entry point)
+-- main.py                      # Engine only
+-- run_api.py                   # API server only
+-- cli.py                       # CLI management tool
+-- config.example.json          # Workflow definitions template
+-- .env.example.sh              # Environment variables template
+-- pyproject.toml               # Python dependencies
+-- src/
|   +-- engine.py                # Orchestration and concurrency
|   +-- scheduler.py             # Cron parsing and scheduling
|   +-- executor.py              # Async command execution
|   +-- database.py              # Legacy SQLite (deprecated, use src/db/)
|   +-- db/
|   |   +-- __init__.py          # Database factory (init_database, get_database)
|   |   +-- database.py          # SQLAlchemy Core (SQLite + PostgreSQL)
|   +-- logger.py                # Per-run and engine logging
|   +-- models.py                # WorkflowRun, Workflow data models
|   +-- api/
|       +-- app.py               # FastAPI application
|       +-- schemas.py           # Pydantic request/response models
|       +-- dependencies.py      # Shared FastAPI dependencies
|       +-- websocket.py         # WebSocket manager
|       +-- auth/                # Authentication module
|       |   +-- routes.py        # Login, register, user CRUD
|       |   +-- models.py        # User model with UserRole enum
|       |   +-- schemas.py       # User, token, role schemas
|       |   +-- dependencies.py  # JWT, password, role guards
|       +-- routes/
|           +-- workflows.py     # Workflow CRUD + trigger
|           +-- runs.py          # Run history + cleanup
|           +-- stats.py         # Engine/workflow statistics
|           +-- logs.py          # Log file access
+-- frontend/                    # React web UI
|   +-- src/
|   |   +-- pages/               # Dashboard, Workflows, Runs, Login, UserManagement
|   |   +-- components/
|   |   |   +-- layout/          # Header, Sidebar, Layout
|   |   |   +-- common/          # StatusBadge, Pagination, ProtectedRoute
|   |   |   +-- dashboard/       # StatusCard, ActivityFeed
|   |   |   +-- workflows/       # WorkflowList, WorkflowCard
|   |   |   +-- runs/            # RunList, RunFilters, CleanupRunsModal
|   |   |   +-- logs/            # LogViewer
|   |   +-- hooks/               # useAuth, useTimezone, useToast, useWebSocket
|   |   +-- services/            # api.ts, auth.ts
|   +-- package.json
+-- data/                        # Auto-created at runtime
    +-- workflows.db             # SQLite database (when using SQLite)
    +-- logs/                    # Per-run log files
```

---

## Troubleshooting

### Authentication Errors ("Could not validate credentials")

1. Ensure you sourced the environment file: `source .env.sh`
2. Verify the key is set: `echo $JWT_SECRET_KEY`
3. If still failing, delete `data/workflows.db` and re-register

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Use a different port
uv run python run_combined.py --port 9000
```

### Missing `triggered_by` Column

If you upgraded from an older version and see `table workflow_runs has no column named triggered_by`:

```bash
sqlite3 data/workflows.db "ALTER TABLE workflow_runs ADD COLUMN triggered_by TEXT;"
```

Or simply restart the backend -- the migration runs automatically on startup.

### Migrating from SQLite to PostgreSQL

1. Install PostgreSQL and create a database
2. Set `DATABASE_URL` in your `.env.sh` or pass `--database-url`
3. Start the engine -- tables are created automatically
4. Note: existing SQLite data is not migrated automatically. Use a migration tool if needed.

### Adding/Modifying Workflows

1. Edit `config.json`
2. Restart the backend (or wait for auto-reload)

---

## Security Notes

- All API endpoints (except `/register` and `/login`) require a valid JWT access token
- The `JWT_SECRET_KEY` **must** be changed in production (use `openssl rand -hex 32`)
- Passwords are hashed with bcrypt before storage
- Access tokens expire after 15 minutes; refresh tokens after 7 days
- The `.env.sh` file is gitignored and must never be committed
- The `data/workflows.db` file contains hashed passwords -- protect it accordingly

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, uvicorn, asyncio |
| Scheduling | APScheduler-style cron parser |
| Database | SQLAlchemy Core (SQLite, PostgreSQL) |
| Auth | JWT (python-jose), bcrypt |
| Frontend | React 18, TypeScript, Vite 5 |
| Styling | Tailwind CSS 3 |
| HTTP Client | Axios |

---

## License

MIT License
