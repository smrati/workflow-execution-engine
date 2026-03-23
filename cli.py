#!/usr/bin/env python3
"""CLI tool for workflow execution engine management."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.database import Database
from src.models import RunStatus


def format_datetime(dt_str: Optional[str]) -> str:
    """Format an ISO datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return dt_str


def format_duration(start_str: str, end_str: Optional[str]) -> str:
    """Calculate and format duration between two datetime strings."""
    if not end_str:
        return "running..."
    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        duration = (end - start).total_seconds()
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration / 60
            return f"{minutes:.1f}m"
        else:
            hours = duration / 3600
            return f"{hours:.1f}h"
    except (ValueError, TypeError):
        return "N/A"


def cmd_status(args):
    """Show engine status and workflow information."""
    db = Database(args.db)
    
    # Get all workflow names that have been run
    workflow_names = db.get_all_workflow_names()
    
    # Try to load current config
    config_path = Path(args.config)
    configured_workflows = []
    
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            configured_workflows = [w.get("name") for w in config if isinstance(w, dict)]
        except (json.JSONDecodeError, IOError):
            pass
    
    print("=" * 60)
    print("WORKFLOW ENGINE STATUS")
    print("=" * 60)
    
    print(f"\nConfig file: {args.config}")
    print(f"Database: {args.db}")
    print(f"Configured workflows: {len(configured_workflows)}")
    print(f"Workflows with history: {len(workflow_names)}")
    
    if configured_workflows:
        print("\n" + "-" * 60)
        print("CONFIGURED WORKFLOWS")
        print("-" * 60)
        
        for name in configured_workflows:
            stats = db.get_workflow_stats(name)
            print(f"\n📋 {name}")
            print(f"   Total runs: {stats['total_runs']}")
            print(f"   ✅ Successful: {stats['successful_runs']}")
            print(f"   ❌ Failed: {stats['failed_runs']}")
            print(f"   ⏱️  Timeout: {stats['timeout_runs']}")
    
    db.close()
    return 0


def cmd_history(args):
    """Show workflow run history."""
    db = Database(args.db)
    
    status_filter = None
    if args.status:
        try:
            status_filter = RunStatus(args.status.lower())
        except ValueError:
            print(f"Invalid status: {args.status}")
            print(f"Valid statuses: {[s.value for s in RunStatus]}")
            db.close()
            return 1
    
    runs = db.get_recent_runs(
        workflow_name=args.workflow,
        status=status_filter,
        limit=args.limit
    )
    
    if not runs:
        print("No runs found.")
        db.close()
        return 0
    
    print("=" * 100)
    print(f"{'ID':<6} {'WORKFLOW':<20} {'STATUS':<10} {'START':<20} {'DURATION':<10} {'EXIT':<5}")
    print("=" * 100)
    
    for run in runs:
        status_icon = "✅" if run.status == RunStatus.SUCCESS else "❌" if run.status == RunStatus.FAILED else "⏱️" if run.status == RunStatus.TIMEOUT else "🔄"
        duration = format_duration(run.start_time.isoformat(), run.end_time.isoformat() if run.end_time else None)
        
        print(f"{run.id:<6} {run.workflow_name:<20} {status_icon} {run.status.value:<8} {format_datetime(run.start_time.isoformat()):<20} {duration:<10} {run.exit_code or 'N/A':<5}")
    
    print("=" * 100)
    print(f"Showing {len(runs)} runs")
    
    db.close()
    return 0


def cmd_logs(args):
    """Show logs for a specific run."""
    db = Database(args.db)
    
    run = db.get_run(args.run_id)
    
    if not run:
        print(f"Run with ID {args.run_id} not found.")
        db.close()
        return 1
    
    print("=" * 80)
    print(f"RUN #{run.id}: {run.workflow_name}")
    print("=" * 80)
    print(f"Command: {run.command}")
    print(f"Status: {run.status.value}")
    print(f"Start: {format_datetime(run.start_time.isoformat())}")
    print(f"End: {format_datetime(run.end_time.isoformat() if run.end_time else None)}")
    print(f"Exit code: {run.exit_code if run.exit_code is not None else 'N/A'}")
    print(f"Attempt: {run.attempt}")
    print(f"Log file: {run.log_file_path}")
    print("=" * 80)
    
    if run.log_file_path and Path(run.log_file_path).exists():
        print("\nLOG CONTENT:")
        print("-" * 80)
        with open(run.log_file_path) as f:
            print(f.read())
    else:
        print("\nLog file not found.")
    
    db.close()
    return 0


def cmd_stats(args):
    """Show statistics for a workflow."""
    db = Database(args.db)
    
    stats = db.get_workflow_stats(args.workflow)
    
    print("=" * 50)
    print(f"STATISTICS: {args.workflow}")
    print("=" * 50)
    
    total = stats['total_runs']
    if total > 0:
        success_rate = (stats['successful_runs'] / total) * 100
    else:
        success_rate = 0
    
    print(f"\nTotal runs: {total}")
    print(f"✅ Successful: {stats['successful_runs']} ({success_rate:.1f}%)")
    print(f"❌ Failed: {stats['failed_runs']}")
    print(f"⏱️  Timeout: {stats['timeout_runs']}")
    
    # Get recent runs for this workflow
    recent = db.get_recent_runs(workflow_name=args.workflow, limit=5)
    
    if recent:
        print("\n" + "-" * 50)
        print("LAST 5 RUNS:")
        print("-" * 50)
        for run in recent:
            status_icon = "✅" if run.status == RunStatus.SUCCESS else "❌"
            print(f"  {status_icon} {format_datetime(run.start_time.isoformat())} - {run.status.value}")
    
    db.close()
    return 0


def cmd_cleanup(args):
    """Clean up old run records."""
    db = Database(args.db)
    
    print(f"Cleaning up runs older than {args.days} days...")
    
    deleted = db.cleanup_old_runs(days_to_keep=args.days)
    
    print(f"Deleted {deleted} old run records.")
    
    db.close()
    return 0


def cmd_list(args):
    """List all workflows with history."""
    db = Database(args.db)
    
    workflow_names = db.get_all_workflow_names()
    
    if not workflow_names:
        print("No workflows found in database.")
        db.close()
        return 0
    
    print("=" * 60)
    print("WORKFLOWS")
    print("=" * 60)
    
    for name in workflow_names:
        stats = db.get_workflow_stats(name)
        success_rate = 0
        if stats['total_runs'] > 0:
            success_rate = (stats['successful_runs'] / stats['total_runs']) * 100
        
        print(f"\n📋 {name}")
        print(f"   Runs: {stats['total_runs']} | Success rate: {success_rate:.1f}%")
    
    db.close()
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Workflow Execution Engine CLI - Manage and monitor workflows"
    )
    
    # Global options
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="Path to config file (default: config.json)"
    )
    parser.add_argument(
        "-d", "--db",
        default="data/workflows.db",
        help="Path to database file (default: data/workflows.db)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Show engine status and workflow information")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show workflow run history")
    history_parser.add_argument(
        "-w", "--workflow",
        help="Filter by workflow name"
    )
    history_parser.add_argument(
        "-s", "--status",
        help="Filter by status (running, success, failed, timeout)"
    )
    history_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=50,
        help="Number of runs to show (default: 50)"
    )
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show logs for a specific run")
    logs_parser.add_argument("run_id", type=int, help="Run ID to show logs for")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics for a workflow")
    stats_parser.add_argument("workflow", help="Workflow name")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old run records")
    cleanup_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Delete runs older than this many days (default: 30)"
    )
    
    # List command
    subparsers.add_parser("list", help="List all workflows with history")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handler
    commands = {
        "status": cmd_status,
        "history": cmd_history,
        "logs": cmd_logs,
        "stats": cmd_stats,
        "cleanup": cmd_cleanup,
        "list": cmd_list,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args) or 0
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
