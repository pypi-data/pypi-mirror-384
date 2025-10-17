import subprocess
from pathlib import Path
from sqlglot import parse_one, exp
import json
import os
from dbt_swap.utils.logging import get_logger
from functools import cached_property

logger = get_logger(__name__)


class DbtSmartBuilder:
    def __init__(self):
        # Allow overriding paths via environment for correctness with dbt --state and target-path
        # DBT_STATE: directory containing a manifest.json representing the comparison state
        # DBT_TARGET_STATE: directory containing the current target manifest.json (after compile)
        self.target_dir = os.environ.get("DBT_TARGET_STATE", "./target")
        self.state_dir = os.environ.get("DBT_STATE", "./state")
        self.target_manifest_path = str(Path(self.target_dir) / "manifest.json")
        self.state_manifest_path = str(Path(self.state_dir) / "manifest.json")
        self.dialect = "postgres"  # Default dialect; could be made configurable

    def list_changed_node_ids(self, downstream: bool = False) -> list[str]:
        """Get list of changed node unique ids using dbt ls command."""
        logger.info("Getting changed nodes...")
        if downstream:
            selector = "state:modified+"
        else:
            selector = "state:modified"
        output = b""
        try:
            output = subprocess.check_output(
                ["dbt", "ls", "--select", selector, "--output", "json", "--quiet"],
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to list changed nodes with dbt: {e}\n"
                f"Command: {e.cmd}\n"
                f"Return code: {e.returncode}\n"
                f"Output: {e.output.decode() if e.output else ''}"
            )
            # If dbt ls fails (e.g., wrong working directory or missing state), treat as no changes
            return []

        if not output.strip():
            return []

        changed_files = [json.loads(line) for line in output.decode().splitlines()]
        changed_node_ids = [node["unique_id"] for node in changed_files]

        return changed_node_ids

    @cached_property
    def modified_node_ids(self) -> list[str]:
        """Get list of changed models using dbt ls command."""
        return self.list_changed_node_ids(downstream=False)

    @cached_property
    def modified_and_downstream_node_ids(self) -> list[str]:
        """Get list of changed models and their downstream dependencies using dbt ls command."""
        return self.list_changed_node_ids(downstream=True)

    def compile_changed_nodes(self) -> None:
        """Compile changed nodes and their dependencies using dbt compile command."""
        logger.info("Compiling changed models and dependencies...")
        subprocess.check_output(
            [
                "dbt",
                "compile",
                "--select",
                "state:modified+",
                "--quiet",
                "--state",
                self.state_dir,
            ]
        )

    def load_manifest(self, manifest_path) -> dict:
        """Load manifest from the given path."""
        path = Path(manifest_path)
        if not path.exists():
            logger.error(f"Manifest not found at {manifest_path}. Run 'dbt compile' first.")
            raise FileNotFoundError(f"Manifest not found at {manifest_path}. Run 'dbt compile' first.")

        with open(path) as f:
            manifest = json.load(f)

        return manifest

    @cached_property
    def manifest(self) -> dict:
        return self.load_manifest(self.target_manifest_path)

    @cached_property
    def compare_manifest(self) -> dict:
        return self.load_manifest(self.state_manifest_path)

    @cached_property
    def nodes(self) -> dict:
        """Get nodes from the target manifest."""
        return self.manifest.get("nodes", {})

    @cached_property
    def compare_nodes(self) -> dict:
        """Get nodes from the state manifest."""
        return self.compare_manifest.get("nodes", {})

    @cached_property
    def child_map(self) -> dict:
        """Return the child map from target manifest."""
        return self.manifest.get("child_map", {})

    def find_changed_columns(self, node: dict) -> list[str]:
        """Find columns that have changed in a node."""
        if node["resource_type"] != "model":
            return []

        sql = node.get("compiled_code", "")
        compare_sql = self.compare_nodes.get(node["unique_id"], {}).get("compiled_code", "select *")

        try:
            parsed = [
                projection
                for select in parse_one(sql, dialect=self.dialect).find_all(exp.Select)
                for projection in select.expressions
            ]
            compare_parsed = [
                projection
                for select in parse_one(compare_sql, dialect=self.dialect).find_all(exp.Select)
                for projection in select.expressions
            ]

            diffs = set(parsed) - set(compare_parsed)
            return [change.alias_or_name for change in diffs]
        except Exception as e:
            logger.warning(f"Could not parse SQL for node {node['name']}: {e}")
            return []

    def find_column_refs(
        self, node: dict, changed_column: str, refs: list[str] | None = None, visited: set[str] | None = None
    ) -> list[str]:
        """Find references to changed columns in a node."""
        if refs is None:
            try:
                sql = node.get("compiled_code", "select *")
            except Exception as e:
                logger.warning(f"Could not get SQL for node {node}: {e}")
                sql = "select *"
            refs = [
                projection
                for select in parse_one(sql, dialect=self.dialect).find_all(exp.Select)
                for projection in select.expressions
            ]
            # If the model selects all columns, consider all changed columns as referenced
            if set(refs) == {exp.Star()}:
                return [changed_column]

        if visited is None:
            visited = set()

        if changed_column in visited:
            return []

        visited.add(changed_column)
        column_refs = []

        for ref in refs:
            if isinstance(ref, exp.Column) and ref.alias_or_name == changed_column:
                column_refs.append(ref.alias_or_name)
            elif isinstance(ref, exp.Alias):
                for col in ref.this.find_all(exp.Column):
                    if col.alias_or_name == changed_column:
                        column_refs.append(ref.alias_or_name)

        # If there are no new column references, return an empty set to avoid infinite recursion
        if column_refs:
            for column_ref in set(column_refs):
                column_refs.extend(self.find_column_refs(node, column_ref, refs, visited))

        # Recursively find column references
        return column_refs

    def search_in_graph(
        self,
        changed_node_id: str,
        changed_columns: list[str],
        visited: set[str] | None = None,
        all: bool = False,
    ) -> list[str]:
        """Recursively search for models affected by column changes."""
        if visited is None:
            visited = set()

        if changed_node_id in visited:
            return []

        visited.add(changed_node_id)
        affected = [changed_node_id]

        for child_id in self.child_map.get(changed_node_id, []):
            if child_id not in visited:
                child_node = self.nodes[child_id]
                # If no specific columns changed, all downstream nodes are affected
                if all:
                    logger.info(
                        f"{child_node['resource_type']} {child_id} is affected by changes in {changed_node_id} (node changed entirely)"
                    )
                    affected.extend(self.search_in_graph(child_id, changed_columns, visited, all=all))
                else:
                    # If the changed_model or child is not a model (e.g., a snapshot or seed), consider it affected
                    if (
                        self.nodes[changed_node_id]["resource_type"] != "model"
                        or child_node["resource_type"] != "model"
                    ):
                        logger.info(
                            f"{child_node['resource_type']} {child_id} is affected by changes in {changed_node_id}"
                        )
                        affected.extend(self.search_in_graph(child_id, changed_columns, visited))
                        continue

                    # If the model selects all columns, consider all changed columns as referenced
                    column_refs = list(
                        {
                            column_ref
                            for changed_column in changed_columns
                            for column_ref in self.find_column_refs(child_node, changed_column)
                        }
                    )

                    # If there are column references, consider the node affected
                    if column_refs:
                        logger.info(
                            f"{child_node['resource_type']} {child_id} is affected by changes in {changed_node_id}, columns: {column_refs}"
                        )
                        affected.extend(self.search_in_graph(child_id, column_refs, visited))

        return list(set(affected))

    def find_modified_nodes(self) -> list[str]:
        """Find all nodes affected by changes."""
        logger.info("🧠 Starting smart model selection...")

        if not self.modified_node_ids:
            logger.info("No modified nodes found.")
            return []

        self.compile_changed_nodes()

        affected_nodes = set()
        for changed_node_id in self.modified_node_ids:
            changed_node = self.nodes[changed_node_id]
            changed_columns = self.find_changed_columns(changed_node)
            column_refs = list(
                {
                    column_ref
                    for changed_column in changed_columns
                    for column_ref in self.find_column_refs(changed_node, changed_column)
                }
            )
            # If no specific columns changed, treat it as a full change
            all = len(changed_columns) == 0
            if all:
                logger.info(f"Changed node: {changed_node['name']}")
            else:
                logger.info(f"Changed model: {changed_node['name']} with changed columns: {column_refs}")

            affected_nodes.update(self.search_in_graph(changed_node_id, column_refs, all=all))

        return list([self.nodes[affected_node]["name"] for affected_node in affected_nodes])
