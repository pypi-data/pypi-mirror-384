"""
Node management commands
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

def build_node_filters(name=None, hostname=None, node_type=None, active=None, tag=None):
    """
    Convert CLI arguments to filter expressions compatible with the project's filter system.
    Returns a dict that can be passed to database plugins or converted to FilterExpressions.
    """
    filters = {}
    
    # Basic string filters (support regex patterns /pattern/)
    if name is not None:
        filters['name'] = name
    if hostname is not None:
        filters['hostname'] = hostname
    if node_type is not None:
        filters['type'] = node_type
        
    # Boolean filters
    if active is not None:
        filters['active'] = active
        
    # List filters (for tags, can be expanded to other list fields)
    if tag is not None and len(tag) > 0:
        # For multiple tags, we might want AND or OR logic
        # This structure allows the database plugin to handle it appropriately
        filters['tags'] = {'in': tag}  # SQL-style "IN" operation
        
    return filters

@app.command("list")
def list_nodes(
    # Basic filters
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter by node name (supports regex /pattern/)"),
    hostname: Optional[str] = typer.Option(None, "--hostname", "-h", help="Filter by hostname (supports regex /pattern/)"),
    node_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by node type"),
    
    # Status filters
    active: Optional[bool] = typer.Option(None, "--active", help="Filter by active status"),
    
    # Advanced filters
    tag: Optional[List[str]] = typer.Option(None, "--tag", help="Filter by tags (can be used multiple times)"),
    
    # Query modifiers
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    sort_by: Optional[str] = typer.Option("name", "--sort", "-s", help="Sort by field (name, hostname, type)"),
    output_format: Optional[str] = typer.Option("table", "--format", "-f", help="Output format (table, json)")
):
    """List nodes with flexible filtering options
    
    Examples:
      acex nodes list --name "router.*" --active
      acex nodes list --type switch --limit 10
      acex nodes list --tag production --tag core --format json
    """
    console.print("Listing nodes...", style="green")
    
    # Build filters using helper function
    filters = build_node_filters(
        name=name,
        hostname=hostname, 
        node_type=node_type,
        active=active,
        tag=tag
    )
    
    # Apply query modifiers
    query_options = {
        'limit': limit,
        'sort_by': sort_by,
        'output_format': output_format
    }
    
    if filters:
        console.print(f"Active filters: {filters}", style="dim")
    if any(v is not None for v in query_options.values()):
        console.print(f"Query options: {query_options}", style="dim")

    
    console.print("Found X nodes matching criteria", style="green")
    
@app.command("create")
def create_node(
    name: str = typer.Argument(..., help="Node name"),
    hostname: Optional[str] = typer.Option(None, "--hostname", "-h", help="Node hostname")
):
    """Create a new node"""
    console.print(f"Creating node: {name}", style="green")
    if hostname:
        console.print(f"Hostname: {hostname}")
    # Implementation would go here

@app.command("show")
def show_node(node_id: int = typer.Argument(..., help="Node ID")):
    """Show node details"""
    console.print(f"Showing node {node_id}", style="green")
    # Implementation would go here
