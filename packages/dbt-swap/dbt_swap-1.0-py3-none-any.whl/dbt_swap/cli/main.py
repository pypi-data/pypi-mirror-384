import typer
from dbt_swap.cli import smart_build
from dbt_swap.cli.common import init_context, set_env

app = typer.Typer(help="dbt-swap CLI — utilities around dbt state and builds")


# Shared context init (runs before each command)
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    target: str = typer.Option(None, help="DBT target name."),
    target_path: str = typer.Option(None, help="Path to dbt target manifest."),
    state: str = typer.Option("target/", help="Path to dbt state manifest."),
):
    """Initialize shared CLI context."""
    ctx.obj = init_context(target=target, target_path=target_path, state=state)
    set_env(target=target, target_path=target_path, state=state)


# Register subcommands
app.command("smart-build")(smart_build.smart_build)

if __name__ == "__main__":
    app()
