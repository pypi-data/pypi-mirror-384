import sys
from importlib.util import find_spec

from rich.console import Console

console = Console()


def check_tc_python_installed() -> bool:
    """Check if TC-Python is installed and available."""
    try:
        spec = find_spec("tc_python")
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def warn_tc_python_not_installed():
    """Display a warning if TC-Python is not installed."""
    if not check_tc_python_installed():
        console.print(
            "\n[yellow]⚠️  Warning:[/yellow] TC-Python is not installed.\n"
            "   Some features may not work correctly.\n"
            "   Install it using: [cyan]tcalc install[/cyan]\n",
            style="yellow",
        )
