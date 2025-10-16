"""
Main CLI application
"""

import typer
from .commands import assets, nodes, logical_nodes

app = typer.Typer(
    name="acex",
    help="ACEX - Extendable Automation & Control Ecosystem CLI",
    add_completion=False
)
state = {"verbose": False}
        
app.add_typer(assets.app, name="assets", help="Manage assets")
app.add_typer(nodes.app, name="nodes", help="Manage nodes") 
app.add_typer(logical_nodes.app, name="logical-nodes", help="Manage logical nodes")


@app.command()
def hello():
    """Test command"""
    typer.echo(f"ACEX!")

# Override the main callback to load commands when needed
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, verbose: bool = False):
    state["verbose"] = verbose
    """Main callback - loads commands only when subcommands are used"""
    if ctx.invoked_subcommand is None:
        # No subcommand specified, show help
        print(ctx.get_help())


if __name__ == "__main__":
    app()
