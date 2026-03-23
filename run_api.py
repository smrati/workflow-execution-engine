"""API-only server entry point.

Use this to run just the API server without the workflow engine.
The engine must be running separately or workflows won't execute.
"""

import argparse
import uvicorn

from src.api.app import create_app
from src.api.dependencies import set_engine


def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description="Workflow Engine API Server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to workflow configuration file"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/workflows.db",
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs",
        help="Directory for log files"
    )

    args = parser.parse_args()

    # Create a read-only engine instance for API access
    from src.engine import Engine
    engine = Engine(
        config_path=args.config,
        db_path=args.db_path,
        log_dir=args.log_dir
    )
    engine.workflows = engine.load_config()

    # Set the engine for API dependencies
    set_engine(engine)

    # Create the app
    app = create_app()

    # Run the server
    uvicorn.run(
        "run_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


app = None

if __name__ == "__main__":
    # Create app for uvicorn
    from src.engine import Engine
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--db-path", type=str, default="data/workflows.db")
    parser.add_argument("--log-dir", type=str, default="data/logs")
    args, _ = parser.parse_known_args()

    engine = Engine(
        config_path=args.config,
        db_path=args.db_path,
        log_dir=args.log_dir
    )
    engine.workflows = engine.load_config()
    set_engine(engine)
    app = create_app()

    main()
