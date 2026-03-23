"""Main entry point for the workflow execution engine."""

import argparse

from src.engine import Engine


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Workflow Execution Engine - A cron-based workflow scheduler"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="Path to the configuration file (default: config.json)"
    )
    parser.add_argument(
        "-d", "--db",
        default="data/workflows.db",
        help="Path to the SQLite database file (default: data/workflows.db)"
    )
    parser.add_argument(
        "-l", "--log-dir",
        default="data/logs",
        help="Path to the log directory (default: data/logs)"
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=1.0,
        help="Check interval in seconds (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Create and run the engine
    engine = Engine(
        config_path=args.config,
        db_path=args.db,
        log_dir=args.log_dir,
        check_interval=args.interval
    )
    
    engine.run()


if __name__ == "__main__":
    main()