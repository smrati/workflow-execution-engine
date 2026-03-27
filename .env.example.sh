# Workflow Execution Engine Environment Variables (Example)
# Copy this file to .env.sh and update the values:
#   cp .env.example.sh .env.sh
# Then source it before running:
#   source .env.sh

# JWT Secret Key - CHANGE THIS IN PRODUCTION!
# Generate a secure random string, e.g.:
#   openssl rand -hex 32
export JWT_SECRET_KEY="your-super-secret-key-change-in-production"

# Optional: API port (default: 8000)
# export API_PORT=8000

# Optional: Database path (default: data/workflows.db)
# export DB_PATH="data/workflows.db"

# Optional: SQLAlchemy database URL (overrides DB_PATH)
# SQLite (default):
#   DATABASE_URL=sqlite+aiosqlite:///data/workflows.db
# PostgreSQL:
#   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/workflow_engine
# export DATABASE_URL="sqlite+aiosqlite:///data/workflows.db"

# Optional: Log directory (default: data/logs)
# export LOG_DIR="data/logs"
