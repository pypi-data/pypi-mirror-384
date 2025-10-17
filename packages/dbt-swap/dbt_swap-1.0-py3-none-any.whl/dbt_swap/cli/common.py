import os

from rich.console import Console

console = Console()


def init_context(target: str, target_path: str, state: str):
    """Initialize shared CLI context."""
    return {
        "target": target,
        "target_path": target_path,
        "state": state,
    }


def set_env(target: str, target_path: str, state: str):
    """Set environment variables for all dbt-swap commands."""
    if target:
        os.environ["DBT_TARGET"] = target
    if target_path:
        os.environ["DBT_TARGET_PATH"] = target_path
    if state:
        os.environ["DBT_STATE_PATH"] = state
