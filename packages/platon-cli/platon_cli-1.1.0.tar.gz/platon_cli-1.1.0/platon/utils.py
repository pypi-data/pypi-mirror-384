"""Utility functions"""

import sys
import json
import yaml
import time
from typing import Any, Dict, List, Callable
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
import questionary

console = Console()


def handle_error(error: Exception):
    """Format and display error"""
    console.print(f"[red]Error:[/red] {str(error)}")

    if hasattr(error, "__cause__") and error.__cause__:
        console.print(f"[yellow]Caused by:[/yellow] {str(error.__cause__)}")

    import traceback
    if console.is_terminal and sys.exc_info()[0] is not None:
        console.print_exception()


def format_output(data: Dict[str, Any], format_type: str) -> str:
    """Format data for output"""
    if format_type == "json":
        return json.dumps(data, indent=2)

    elif format_type == "yaml":
        return yaml.dump(data, default_flow_style=False)

    elif format_type == "env" or format_type == "dotenv":
        lines = []
        for key, value in data.items():
            if " " in str(value) or '"' in str(value):
                value = f'"{value}"'
            lines.append(f"{key}={value}")
        return "\n".join(lines)

    elif format_type == "table":
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        for key, value in data.items():
            table.add_row(key, str(value))

        with console.capture() as capture:
            console.print(table)
        return capture.get()

    else:
        return str(data)


def export_to_file(content: str, file_path: Path, format_type: str):
    """Export content to file"""
    path = Path(file_path)

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(content)


def watch_logs(callback: Callable, interval: float = 2.0):
    """Watch and display updates"""
    try:
        with Live(Spinner("dots", text="Watching..."), console=console) as live:
            while True:
                try:
                    result = callback()
                    live.update(result)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    live.update(f"[red]Error:[/red] {e}")

                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching[/yellow]")


def fuzzy_select(choices: List[str], message: str = "Select:") -> str:
    """Fuzzy select from list"""
    if not choices:
        raise ValueError("No choices provided")

    if len(choices) == 1:
        return choices[0]

    return questionary.autocomplete(
        message,
        choices=choices,
        style=questionary.Style([
            ("qmark", "fg:cyan bold"),
            ("question", "bold"),
            ("pointer", "fg:cyan bold"),
            ("highlighted", "fg:cyan bold"),
            ("selected", "fg:green"),
        ]),
    ).ask()


def confirm(message: str, default: bool = False) -> bool:
    """Confirmation prompt"""
    return questionary.confirm(message, default=default).ask()


def prompt(message: str, password: bool = False) -> str:
    """Text input prompt"""
    if password:
        return questionary.password(message).ask()
    return questionary.text(message).ask()


def diff_dict(old: Dict, new: Dict) -> str:
    """Generate diff between two dictionaries"""
    lines = []

    all_keys = set(old.keys()) | set(new.keys())

    for key in sorted(all_keys):
        old_val = old.get(key)
        new_val = new.get(key)

        if key not in old:
            lines.append(f"+ {key}={new_val}")
        elif key not in new:
            lines.append(f"- {key}={old_val}")
        elif old_val != new_val:
            lines.append(f"- {key}={old_val}")
            lines.append(f"+ {key}={new_val}")

    return "\n".join(lines)


def parse_key_value_args(args: List[str]) -> Dict[str, str]:
    """Parse key=value arguments"""
    result = {}

    for arg in args:
        if "=" not in arg:
            raise ValueError(f"Invalid argument format: {arg}. Expected key=value")

        key, value = arg.split("=", 1)
        result[key] = value

    return result


def mask_secret(value: str, show_chars: int = 4) -> str:
    """Mask secret value"""
    if len(value) <= show_chars:
        return "*" * len(value)

    return value[:show_chars] + "*" * (len(value) - show_chars)


def format_age(timestamp: str) -> str:
    """Format timestamp as relative age"""
    from datetime import datetime, timezone

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt

        if delta.days > 365:
            return f"{delta.days // 365}y"
        elif delta.days > 0:
            return f"{delta.days}d"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m"
        else:
            return f"{delta.seconds}s"
    except Exception:
        return timestamp


def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


def print_syntax(code: str, language: str = "yaml"):
    """Print syntax highlighted code"""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def success(message: str):
    """Print success message"""
    console.print(f"[green]✓[/green] {message}")


def warning(message: str):
    """Print warning message"""
    console.print(f"[yellow]⚠[/yellow] {message}")


def error(message: str):
    """Print error message"""
    console.print(f"[red]✗[/red] {message}")


def info(message: str):
    """Print info message"""
    console.print(f"[blue]ℹ[/blue] {message}")


def parse_file_to_dict(file_path: str, format_type: str) -> Dict[str, str]:
    """Parse file content to dictionary based on format type"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text()

    if format_type == "json":
        data = json.loads(content)
        return {k: str(v) for k, v in data.items()}

    elif format_type == "yaml":
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError("YAML file must contain a dictionary")
        return {k: str(v) for k, v in data.items()}

    elif format_type in ("env", "dotenv"):
        from dotenv import dotenv_values
        env_vars = dotenv_values(file_path)
        return {k: str(v) for k, v in env_vars.items() if v is not None}

    else:
        raise ValueError(f"Unsupported format: {format_type}")
