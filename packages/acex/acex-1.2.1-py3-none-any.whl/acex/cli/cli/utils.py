"""
CLI utilities and helpers
"""

from typing import Optional, Any, Dict
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

def print_success(message: str):
    """Print success message"""
    console.print(f"✅ {message}", style="green")

def print_error(message: str):
    """Print error message"""
    console.print(f"❌ {message}", style="red")

def print_warning(message: str):
    """Print warning message"""
    console.print(f"⚠️  {message}", style="yellow")

def print_info(message: str):
    """Print info message"""
    console.print(f"ℹ️  {message}", style="blue")

def create_table(title: str, columns: list) -> Table:
    """Create a Rich table with standard formatting"""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column)
    return table

def display_model_data(data: Any, title: str = "Data"):
    """Display model data in a formatted way"""
    if hasattr(data, 'dict'):
        # SQLModel/Pydantic model
        rprint({title: data.dict()})
    elif isinstance(data, dict):
        rprint({title: data})
    else:
        rprint({title: str(data)})
