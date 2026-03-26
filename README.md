# Workflow Execution Engine

A cron-based workflow execution engine for scheduling and running commands with a modern web UI for monitoring and management.

## Features

- **Cron-based Scheduling**: Use standard cron expressions to define when workflows should run
- **Parallel Execution**: Multiple workflows can run concurrently
- **Persistent Metadata**: All run history stored in SQLite database
- **Detailed Logging**: Each workflow run gets its own timestamped log file
- **Web UI**: Modern React-based dashboard for monitoring and managing workflows
- **REST API**: Full-featured API for programmatic access
- **Real-time Updates**: WebSocket support for live status updates
- **Graceful Shutdown**: Handles SIGINT/SIGTERM for clean shutdown
- **Authentication**: JWT-based authentication for secure access

## Authentication

The system uses **JWT (JSON Web Token)** based authentication with role-based access control.

### User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **admin** | Administrator | Full access + user management |
| **normal** | Regular user | Access to workflows and runs |

### Role-Based Access Control

- **First user registration** → automatically becomes **admin**
- **Subsequent registrations** → disabled (admin must create users)
- **Admin users** can:
  - Create new users (admin or normal role)
  - Update user roles
  - Delete users
  - Access all normal user features
- **Normal users** can:
  - View workflows and runs
  - Trigger workflow executions
  - Enable/disable workflows

### Authentication Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/auth/register` | Register first user (admin) | Public (first user only) |
| POST | `/api/auth/login` | Login and get tokens | Public |
| POST | `/api/auth/refresh` | Refresh access token | Public (with refresh token) |
| GET | `/api/auth/me` | Get current user info | Authenticated |
| POST | `/api/auth/users` | Create new user | Admin only |
| GET | `/api/auth/users` | List all users | Admin only |
| PUT | `/api/auth/users/{id}/role` | Update user role | Admin only |
| DELETE | `/api/auth/users/{id}` | Delete user | Admin only |

### Token Types

- **Access Token**: Valid for 15 minutes, used for API authentication
- **Refresh Token**: Valid for 7 days, used to obtain new access tokens

### First-Time Setup

1. Start the backend server
2. Navigate to `http://localhost:5173`
3. The first registration will create an **admin** account
4. All subsequent registrations are disabled
5. Admin can create additional users via the User Management page

### Creating Users as Admin

1. Login with admin account
2. Click "User Management" in the header
3. Click "Create User"
4. Enter username, password, and select role
5. Click "Create User"

### Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Login     │────►│  Get Token  │────►│   Access    │
│  (username/ │     │ (access +   │     │   Protected │
│   password) │     │  refresh)   │     │   Routes    │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Token      │
                   │   Refresh    │
                   │ (auto renew) │
                   └─────────────┘
```

### Security Notes

- All `/api/auth/*` endpoints except `/register` (after first user) and `/login` are public
- All other `/api/*` endpoints require a valid JWT access token
- Tokens are stored in browser localStorage
- The `Authorization: Bearer <token>` header is automatically added to all API requests
- Sessions expire after 15 minutes of inactivity (access token)
- Users are stored in the `users` table in SQLite database
- First user is automatically assigned the **admin** role

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT signing | `your-secret-key-change-in-production` |

**Important**: Change `JWT_SECRET_KEY` in production environments!

## Architecture Overview

The system consists of **two separate components** that work together:

### 1. Backend Server (`run_combined.py`)
When you run `uv run python run_combined.py --port 8000 --config config.json`, it starts:

| Component | Description |
|-----------|-------------|
| **Workflow Engine** | Executes scheduled workflows based on cron expressions from `config.json` |
| **API Server** | REST API on port 8000 for programmatic access |
| **WebSocket Server** | Real-time updates at `/ws` endpoint |
| **Database** | SQLite storage for run history in `data/workflows.db` |
| **Log Files** | Timestamped logs for each workflow run in `data/logs/` |

**What happens when you run it:**
1. Loads workflow definitions from `config.json`
2. Schedules workflows based on their cron expressions
3. Executes workflows when they become due
4. Stores all run metadata and logs
5. Serves REST API endpoints at `http://localhost:8000`
6. Broadcasts real-time updates via WebSocket

### 2. Frontend Dashboard (`frontend/`)
A **separate React application** that provides the web UI:

- **Must be started independently** with `cd frontend && npm run dev`
- Runs on `http://localhost:5173`
- Connects to the backend API at `http://localhost:8000`
- Displays workflows, run history, logs, and real-time updates

### Connection Diagram
```
┌─────────────────┐         ┌─────────────────┐
│   Frontend UI   │  HTTP   │  Backend Server │
│  (React + Vite) │◄───────►│ (FastAPI +      │
│  :5173          │  WS     │  Workflow Engine)│
└─────────────────┘         │  :8000          │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │ config.json     │
                            │ workflows.db    │
                            │ logs/           │
                            └─────────────────┘
```

## How to Run the System

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- uv (Python package manager)

### Environment Setup

Before running the system, you need to configure environment variables:

1. **Copy the example file**:
   ```bash
   cp .env.example.sh .env.sh
   ```

2. **Edit `.env.sh` and set your values**:
   ```bash
   nano .env.sh  # or your preferred editor
   ```

3. **Generate a secure JWT secret key**:
   ```bash
   openssl rand -hex 32
   ```
   Copy the output and set it as `JWT_SECRET_KEY` in `.env.sh`

4. **Source the environment file before starting**:
   ```bash
   source .env.sh
   ```

**Important**: The `.env.sh` file is in `.gitignore` and will not be committed to version control.

### Required Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | **Yes** | `your-secret-key-change-in-production` |

### Quick Start (Two Terminals)

**Step 0: Setup Environment**
```bash
# Copy and configure environment
cp .env.example.sh .env.sh
nano .env.sh  # Set your JWT_SECRET_KEY
source .env.sh
```

**Step 1: Install Dependencies**
```bash
# Backend dependencies
uv sync

# Frontend dependencies
cd frontend && npm install && cd ..
```

**Step 2: Start Backend (Terminal 1)**
```bash
uv run python run_combined.py
```

**Step 3: Start Frontend (Terminal 2)**
```bash
cd frontend && npm run dev
```

**Step 4: Access the Application**

| Service | URL |
|---------|-----|
| **Web UI** | http://localhost:5173 |
| **API Server** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

### Verify It's Working
```bash
# Check API is running
curl http://localhost:8000/api/stats/engine

# Check workflows are loaded
curl http://localhost:8000/api/workflows
```

### Alternative: Engine Only (No UI)

If you just want the workflow engine without the web interface:

```bash
uv run python main.py
```

---

## Web UI

The workflow engine includes a modern web-based interface for monitoring and managing your workflows.

### Access URLs

| Service | URL |
|---------|-----|
| Web UI (Frontend) | http://localhost:5173 |
| API Server | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| WebSocket | ws://localhost:8000/ws |

### UI Features

#### Dashboard
- **Status Cards**: Quick overview of total workflows, enabled workflows, total runs, success rate, and currently running tasks
- **Activity Feed**: Real-time list of recent workflow executions with status indicators
- **Auto-refresh**: Dashboard updates automatically via WebSocket when runs complete

#### Workflows Page
- List all configured workflows in a table format
- View workflow name, schedule (cron), status (enabled/disabled), and next run time
- **Run Now**: Manually trigger a workflow execution
- Click workflow name to view detailed information

#### Workflow Detail Page
- View full workflow configuration (command, schedule, timeout, retries)
- See workflow statistics (total runs, success/fail/timeout counts)
- Enable or disable the workflow
- Trigger manual runs

#### Runs Page
- View complete history of all workflow executions
- **Filter by workflow name**
- **Filter by status** (running, success, failed, timeout, retry)
- **Pagination** for large datasets
- Click any run to view details

#### Run Detail Page
- View run metadata (workflow, command, start/end time, duration, exit code)
- **Log Viewer**: Full log output from the workflow execution
- Status badge with color coding

### Real-time Updates

The UI receives real-time updates via WebSocket when:
- A workflow run starts
- A workflow run completes
- Workflow configurations are reloaded

---

## Setup Guide

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- uv (Python package manager)

### Full Setup (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd workflow-execution-engine

# 2. Setup environment variables
cp .env.example.sh .env.sh
# Edit .env.sh and set your JWT_SECRET_KEY (use: openssl rand -hex 32)
source .env.sh

# 3. Install Python dependencies
uv sync

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Create your config.json from the example
cp config.example.json config.json

# 6. Start the combined server (Engine + API)
uv run python run_combined.py

# 7. In a new terminal, start the frontend
cd frontend && npm run dev
```

### Environment Variables Setup

Before running the system, you must configure the environment variables:

1. **Copy the example file:**
   ```bash
   cp .env.example.sh .env.sh
   ```

2. **Edit `.env.sh` and set your values:**
   ```bash
   nano .env.sh
   ```

3. **Generate a secure JWT secret key:**
   ```bash
   openssl rand -hex 32
   ```

4. **Source the environment file before starting:**
   ```bash
   source .env.sh
   ```

### Required Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | **Yes** | `your-secret-key-change-in-production` |

**⚠️ Important**: 
- **Never commit `.env.sh` to version control** (it's in `.gitignore`)
- Always use a strong, unique `JWT_SECRET_KEY` in production
- Source `.env.sh` in every terminal before running the application

### Access the Application

1. Open your browser to **http://localhost:5173**
2. The API is available at **http://localhost:8000**
3. API documentation at **http://localhost:8000/docs**

---

## Running Options

### Option 1: Combined Mode (Recommended for Development)

Runs both the workflow engine and API server in one process:

```bash
uv run python run_combined.py --port 8000 --config config.json
```

### Option 2: Engine Only

Just the workflow scheduler without the web interface:

```bash
uv run python main.py --config config.json
```

### Option 3: API Only

Run just the API server (useful if engine is running separately):

```bash
uv run python run_api.py --port 8000
```

## Configuration

Create a `config.json` file from the example template:

```bash
cp config.example.json config.json
```

The config file should contain a JSON array of workflow objects:

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
| `timeout` | integer | No | Timeout in seconds (default: none) |
| `retry_count` | integer | No | Number of retries on failure (default: 0) |
| `retry_delay` | integer | No | Delay between retries in seconds (default: 60) |
| `working_dir` | string | No | Working directory for command execution |
| `env` | object | No | Environment variables to set |

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

### CLI Management Tool

```bash
# Show engine status
uv run python cli.py status

# Show run history
uv run python cli.py history

# Filter history by workflow
uv run python cli.py history -w hello-world

# Filter by status
uv run python cli.py history -s failed

# Show logs for a specific run
uv run python cli.py logs 123

# Show workflow statistics
uv run python cli.py stats hello-world

# List all workflows
uv run python cli.py list

# Clean up old records
uv run python cli.py cleanup --days 30
```

### Stop the Engine

Press `Ctrl+C` or send `SIGTERM` to gracefully shutdown the engine. It will wait for running tasks to complete before exiting.

## Project Structure

```
workflow-execution-engine/
├── main.py                 # Engine entry point
├── run_combined.py         # Combined engine + API runner
├── run_api.py              # API-only server
├── cli.py                  # CLI management tool
├── config.example.json      # Workflow definitions (template)
├── .env.example.sh         # Environment variables (template)
├── .env.sh                 # Environment variables (local, gitignored)
├── pyproject.toml          # Project configuration
├── src/
│   ├── __init__.py
│   ├── engine.py           # Main orchestration logic
│   ├── scheduler.py        # Cron parsing & scheduling
│   ├── executor.py         # Async command execution
│   ├── database.py         # SQLite operations
│   ├── logger.py           # Logging setup
│   ├── models.py           # Data models
│   └── api/                # FastAPI web interface
│       ├── __init__.py
│       ├── app.py          # FastAPI application factory
│       ├── schemas.py      # Pydantic models
│       ├── dependencies.py # Engine access
│       ├── websocket.py    # WebSocket manager
│       ├── auth/           # Authentication module
│       │   ├── __init__.py
│       │   ├── routes.py   # Auth endpoints
│       │   ├── models.py   # User model
│       │   ├── schemas.py  # Auth schemas
│       │   └── dependencies.py # Auth dependencies
│       └── routes/
│           ├── workflows.py
│           ├── runs.py
│           ├── stats.py
│           └── logs.py
├── frontend/               # React web UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/     # Header, Sidebar, Layout
│   │   │   ├── common/     # StatusBadge, Pagination, ProtectedRoute
│   │   │   ├── dashboard/  # StatusCard, ActivityFeed
│   │   │   ├── workflows/  # WorkflowList, WorkflowCard
│   │   │   ├── runs/       # RunList, RunFilters
│   │   │   └── logs/       # LogViewer
│   │   ├── pages/          # Dashboard, Workflows, Runs, Login, UserManagement
│   │   ├── hooks/          # useWebSocket, useAuth
│   │   └── services/       # API client, auth API
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── workflows.db        # SQLite database (auto-created)
│   └── logs/               # Log files (auto-created)
│       ├── engine.log      # Engine activity log
│       └── {workflow_name}/
│           └── {timestamp}.log
└── README.md
```

## API Reference

### Authentication Endpoints (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register first user (becomes admin) |
| POST | `/api/auth/login` | Login and get access token |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user info |

### Admin-Only Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/users` | Create new user |
| GET | `/api/auth/users` | List all users |
| PUT | `/api/auth/users/{id}/role` | Update user role |
| DELETE | `/api/auth/users/{id}` | Delete user |

### Workflow Endpoints (Protected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows` | List all workflows |
| GET | `/api/workflows/{name}` | Get workflow details with stats |
| GET | `/api/workflows/{name}/schedule` | Get schedule information |
| POST | `/api/workflows/{name}/run` | Trigger manual run |
| PUT | `/api/workflows/{name}/enable` | Enable a workflow |
| PUT | `/api/workflows/{name}/disable` | Disable a workflow |
| GET | `/api/runs` | List runs (paginated, filterable) |
| GET | `/api/runs/{id}` | Get specific run details |
| GET | `/api/stats/engine` | Get engine status |
| GET | `/api/stats/overview` | Get dashboard overview |
| GET | `/api/stats/workflows/{name}` | Get workflow statistics |
| GET | `/api/logs/{run_id}` | Get log content for a run |
| WS | `/ws` | WebSocket for real-time updates |

### WebSocket Events

The WebSocket endpoint (`/ws`) broadcasts the following event types:

| Event Type | Description |
|------------|-------------|
| `run_started` | A workflow run has started |
| `run_completed` | A workflow run has finished |
| `workflow_event` | Workflow added/removed/modified/enabled/disabled |
| `stats_update` | Statistics have changed |

---

## Database Schema

### `users` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| hashed_password | TEXT | Bcrypt hashed password |
| role | TEXT | User role (`admin` or `normal`) |
| created_at | TEXT | ISO format timestamp |

### `workflow_runs` Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| workflow_name | TEXT | Name of the workflow |
| command | TEXT | Command that was executed |
| start_time | TEXT | ISO format timestamp |
| end_time | TEXT | ISO format timestamp (nullable) |
| exit_code | INTEGER | Process exit code (nullable) |
| status | TEXT | running, success, failed, or timeout |
| log_file_path | TEXT | Path to the log file |
| attempt | INTEGER | Retry attempt number |

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

```

### Troubleshooting

#### Authentication Errors

If you see authentication errors or "Could not validate credentials":

1. **Ensure you sourced the environment file**
   ```bash
   source .env.sh
   ```

2. **Verify JWT_SECRET_KEY is set**
   ```bash
   echo $JWT_SECRET_KEY
   ```

3. **If problems persist, reset:**
   - Delete `data/workflows.db`
   - Restart the application
   - Re-register users

### Adding New Workflows

1. Edit `config.json`
2. Add a new workflow object with required fields
3. The engine will auto-reload within 5 seconds (or restart manually)

## License

MIT License
