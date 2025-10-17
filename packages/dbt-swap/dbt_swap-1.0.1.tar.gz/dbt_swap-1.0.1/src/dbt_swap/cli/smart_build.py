import typer
import subprocess
from dbt_swap.core.smart_builder import DbtSmartBuilder
from dbt_swap.utils.logging import get_logger

logger = get_logger(__name__)


app = typer.Typer(help="Build only modified models intelligently.")


@app.command("smart-build")
def smart_build(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, help="Perform a dry run without making changes."),
    verbose: bool = typer.Option(False, help="Enable verbose output."),
):
    """
    Run a smart build — builds only modified models based on dbt state and column level lineage.
    Additional arguments after `smart-build` are passed directly to `dbt build`.
    """

    dbt_smart_build = DbtSmartBuilder()
    modified_nodes = dbt_smart_build.find_modified_nodes()

    if ctx.args:
        args = ctx.args
    else:
        args = []

    command = f"dbt build -s {' '.join(modified_nodes)} {' '.join(args)}"

    if dry_run:
        resource_types = {node["resource_type"] for node in dbt_smart_build.nodes.values()}
        resource_type_counts = {
            resource_type: {
                "smart_count": sum(
                    1 for node in modified_nodes if dbt_smart_build.nodes[node]["resource_type"] == resource_type
                ),
                "total_count": sum(
                    1
                    for node in dbt_smart_build.modified_and_downstream_node_ids
                    if dbt_smart_build.nodes[node]["resource_type"] == resource_type
                ),
            }
            for resource_type in resource_types
        }
        for resource_type, counts in resource_type_counts.items():
            if counts["total_count"] > 0:
                logger.info(f"[DRY RUN] Would build {counts['smart_count']}/{counts['total_count']} {resource_type}(s)")
        if verbose:
            logger.info("[DRY RUN] Would build:")
            for modified_node in modified_nodes:
                logger.info(modified_node)
    else:
        subprocess.run(command, shell=True, check=True)
