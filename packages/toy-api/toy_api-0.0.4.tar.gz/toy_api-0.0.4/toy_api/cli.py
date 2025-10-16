#!/usr/bin/env python3
"""

CLI for Toy API

Launch configurable toy APIs from YAML configuration files and generate dummy data tables.

License: BSD 3-Clause

"""
#
# IMPORTS
#
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click

from toy_api.app import _load_config, create_app
from toy_api.config_discovery import find_config_path, get_available_configs, init_config_with_example
from toy_api.constants import DEFAULT_HOST
from toy_api.port_utils import get_port_from_config_or_auto
from toy_api.process_manager import get_all_configs_in_directory, list_processes, start_background_process, stop_all_processes, stop_process


#
# MAIN CLI GROUP
#
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Toy API - Configurable test API servers and dummy data generation.

    Run without a command to list available configurations.
    """
    if ctx.invoked_subcommand is None:
        _list_api_configs()
        _list_database_configs()


#
# COMMANDS
#
@cli.command()
def init() -> None:
    """Initialize toy_api_config directory with example configuration."""
    if init_config_with_example():
        click.echo("✓ Created toy_api_config/ directory")
        click.echo("✓ Created toy_api_config/databases/ subdirectory")
        click.echo("✓ Created toy_api_config/apis/ subdirectory")
        click.echo("✓ Copied v1.yaml to toy_api_config/apis/example.yaml")
        click.echo()
        click.echo("You can now customize example.yaml or add more configs:")
        click.echo("  toy_api start example    # Use the example config")
        click.echo("  cp <other_configs> toy_api_config/apis/")
    else:
        click.echo("Error: Could not initialize toy_api_config/ directory", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config", required=False, default="v1", type=str)
@click.option("--host", default=DEFAULT_HOST, help=f"Host to bind to (default: {DEFAULT_HOST})")
@click.option("-p", "--port", type=int, help="Port to bind to (overrides config file)")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--all", "start_all", is_flag=True, help="Start all servers in config directory")
@click.option("--out", type=str, help="With --all, print output for specific config (default: last)")
def start(config: str, host: str, port: Optional[int], debug: bool, start_all: bool, out: Optional[str]) -> None:
    """Start toy API server with specified configuration.

    CONFIG: Config name, path, or directory for --all (default: v1)

    Examples:
      toy_api start
      toy_api start v2
      toy_api start custom_config --port 5000
      toy_api start --all
      toy_api start --all versioned_remote
      toy_api start --all versioned_remote --out versioned_remote/0.1
    """
    if start_all:
        _start_all_servers(config if config != "v1" else None, host, out)
        return

    try:
        # Find config file using discovery system
        config_path, config_message = find_config_path(config)

        if not config_path:
            click.echo(f"Error: {config_message}", err=True)
            click.echo("\nAvailable configs:")
            list_configs(apis=True, tables=False)
            sys.exit(1)

        # Create Flask app from discovered config
        app = create_app(config_path)

        # Load config for port determination
        app_config = {}
        try:
            app_config = _load_config(config_path)
        except Exception as e:
            click.echo(f"Warning: Could not load config file: {e}")

        # Determine port using smart port logic
        final_port, port_message = get_port_from_config_or_auto(app_config, port, host)

        if final_port == 0:
            click.echo(f"Error: {port_message}", err=True)
            sys.exit(1)

        click.echo("Starting toy API...")
        click.echo(f"Config: {config_message}")
        if port_message:
            click.echo(f"Port: {port_message}")
        click.echo(f"Server: http://{host}:{final_port}")
        click.echo("Press Ctrl+C to stop")

        # Start the server
        app.run(host=host, port=final_port, debug=debug)

    except FileNotFoundError as e:
        click.echo(f"Error: Configuration file not found: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(name="list")
@click.option("--apis", is_flag=True, help="List only API configurations")
@click.option("--tables", is_flag=True, help="List only table configurations")
def list_configs(apis: bool, tables: bool) -> None:
    """List available API and table configurations."""
    # If neither flag specified, show both
    if not apis and not tables:
        apis = True
        tables = True

    if apis:
        _list_api_configs()

    if tables:
        _list_database_configs()


@cli.command()
@click.argument("database_config", required=False, type=str)
@click.option("--tables", type=str, help="Comma-separated list of tables to generate (default: all)")
@click.option("--dest", "-d", type=str, help="Destination directory (default: databases/<config_path>/)")
@click.option("--type", "-t", type=click.Choice(['parquet', 'csv', 'json', 'ld-json']),
              default='parquet', help="Output file format")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
@click.option("--partition", multiple=True, help="Partition columns (parquet only)")
@click.option("--all", "generate_all", is_flag=True, help="Generate all database configs")
def database(database_config: Optional[str], tables: Optional[str], dest: Optional[str],
             type: str, force: bool, partition: tuple, generate_all: bool) -> None:
    """Generate tables from database configuration file.

    DATABASE_CONFIG: Database config name or path (e.g., test_db or versioned_db/1.2)

    Examples:
      toy_api database test_db
      toy_api database test_db --tables posts
      toy_api database test_db --tables posts,users
      toy_api database test_db --dest output/ --type csv --force
      toy_api database --all
      toy_api database --all versioned_db
    """
    from toy_api.table_generator import create_table

    # Handle --all flag
    if generate_all:
        _generate_all_databases(database_config, type, force, list(partition) if partition else None)
        return

    # Require database_config if not using --all
    if not database_config:
        click.echo("Error: DATABASE_CONFIG required when not using --all", err=True)
        click.echo("Usage: toy_api database <config> or toy_api database --all")
        sys.exit(1)

    try:
        # Find database config file
        config_path = _find_database_config(database_config)

        if not config_path:
            click.echo(f"Error: Database config '{database_config}' not found", err=True)
            click.echo("\nAvailable database configs:")
            _list_database_configs()
            sys.exit(1)

        # Determine destination
        if dest is None:
            # Derive output path from config path structure
            # toy_api_config/databases/test_db.yaml -> databases/test_db/
            # toy_api_config/databases/versioned_db/1.2.yaml -> databases/versioned_db/1.2/
            config_path_obj = Path(config_path)

            # Get the part after "databases/"
            parts = config_path_obj.parts
            if 'databases' in parts:
                db_index = parts.index('databases')
                # Get everything after 'databases' and before the .yaml file
                db_path_parts = parts[db_index + 1:]
                # Remove .yaml extension from last part
                db_path_parts = list(db_path_parts)
                db_path_parts[-1] = db_path_parts[-1].replace('.yaml', '')
                # Construct destination: databases/test_db/ or databases/versioned_db/1.2/
                dest = str(Path('databases') / Path(*db_path_parts))
            else:
                # Fallback if 'databases' not in path
                dest = str(Path('databases') / config_path_obj.stem)

        dest_dir = Path(dest)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Convert partition tuple to list
        partition_cols = list(partition) if partition else None

        # Parse tables filter
        tables_filter = None
        if tables:
            tables_filter = [t.strip() for t in tables.split(',')]

        # Generate table(s)
        click.echo(f"Generating tables from {config_path}...")
        create_table(
            table_config=config_path,
            dest=str(dest_dir),
            file_type=type,
            partition_cols=partition_cols,
            tables_filter=tables_filter,
            force=force
        )

        click.echo(f"✓ Tables written to {dest_dir}/")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config", required=False, type=str)
@click.option("--all", "stop_all", is_flag=True, help="Stop all running servers")
def stop(config: Optional[str], stop_all: bool) -> None:
    """Stop running toy API server(s).

    CONFIG: Config name to stop (e.g., basic, versioned_remote/0.1)

    Examples:
      toy_api stop basic
      toy_api stop versioned_remote/0.1
      toy_api stop --all
      toy_api stop --all versioned_remote
    """
    if stop_all:
        if config:
            # Stop all servers matching a prefix
            _stop_servers_by_prefix(config)
        else:
            # Stop all servers
            results = stop_all_processes()
            if not results:
                click.echo("No running servers found")
                return

            for config_name, success, message in results:
                if success:
                    click.echo(f"✓ {message}")
                else:
                    click.echo(f"✗ {message}", err=True)
        return

    if not config:
        click.echo("Error: CONFIG required when not using --all", err=True)
        click.echo("Usage: toy_api stop <config> or toy_api stop --all")
        sys.exit(1)

    success, message = stop_process(config)
    if success:
        click.echo(f"✓ {message}")
    else:
        click.echo(f"✗ {message}", err=True)
        sys.exit(1)


@cli.command()
def ps() -> None:
    """List running toy API servers."""
    processes = list_processes()

    if not processes:
        click.echo("No running servers")
        return

    click.echo("Running servers:")
    click.echo()
    for config_name, info in sorted(processes.items()):
        click.echo(f"  {config_name}")
        click.echo(f"    URL: http://{info['host']}:{info['port']}")
        click.echo(f"    PID: {info['pid']}")
        click.echo(f"    Log: {info['log_file']}")
        click.echo()


#
# INTERNAL HELPERS
#
def _start_all_servers(directory: Optional[str], host: str, out_config: Optional[str]) -> None:
    """Start all servers in a directory (or subdirectory).

    Args:
        directory: Directory to search (None = all configs, or specific subdirectory).
        host: Host to bind to.
        out_config: Config to print output for (None = last server).
    """
    # Determine search directory
    if directory:
        # Check if it's a subdirectory (e.g., "versioned_remote")
        from pathlib import Path
        subdir_path = Path(f"toy_api_config/apis/{directory}")
        if subdir_path.is_dir():
            search_dir = str(subdir_path)
        else:
            search_dir = "toy_api_config/apis"
    else:
        search_dir = "toy_api_config/apis"

    # Get all configs
    configs = get_all_configs_in_directory(search_dir)

    if not configs:
        click.echo(f"No configs found in {search_dir}")
        sys.exit(1)

    # Filter by prefix if directory was specified
    if directory and not Path(f"toy_api_config/apis/{directory}").is_dir():
        configs = [(name, path) for name, path in configs if name.startswith(directory)]
        if not configs:
            click.echo(f"No configs found matching '{directory}'")
            sys.exit(1)

    click.echo(f"Starting {len(configs)} server(s)...")
    click.echo()

    started = []
    target_config = out_config if out_config else configs[-1][0]

    for config_name, config_path in configs:
        try:
            # Load config for port
            config_data = _load_config(config_path)
            port, port_msg = get_port_from_config_or_auto(config_data, None, host)

            if port == 0:
                click.echo(f"✗ {config_name}: {port_msg}")
                continue

            # Start in background
            success, message = start_background_process(config_name, host, port)

            if success:
                click.echo(f"✓ {message}")
                started.append((config_name, host, port))
            else:
                click.echo(f"✗ {message}")

        except Exception as e:
            click.echo(f"✗ {config_name}: {e}")

    click.echo()
    click.echo(f"Started {len(started)} server(s)")

    # Print output for target config
    if target_config and any(name == target_config for name, _, _ in started):
        target_info = next((h, p) for n, h, p in started if n == target_config)
        click.echo()
        click.echo(f"Output for {target_config}:")
        click.echo(f"  http://{target_info[0]}:{target_info[1]}")


def _stop_servers_by_prefix(prefix: str) -> None:
    """Stop all servers matching a prefix.

    Args:
        prefix: Prefix to match (e.g., "versioned_remote").
    """
    processes = list_processes()
    matching = [(name, info) for name, info in processes.items() if name.startswith(prefix)]

    if not matching:
        click.echo(f"No running servers found matching '{prefix}'")
        return

    click.echo(f"Stopping {len(matching)} server(s) matching '{prefix}'...")
    click.echo()

    for config_name, _ in matching:
        success, message = stop_process(config_name)
        if success:
            click.echo(f"✓ {message}")
        else:
            click.echo(f"✗ {message}", err=True)


def _list_api_configs() -> None:
    """List available API configuration files."""
    click.echo("API Configurations:")
    click.echo()

    configs = get_available_configs()

    # Show local configs first
    if configs["local"]:
        click.echo("📁 Local configs (toy_api_config/apis/):")
        for config_name in sorted(configs["local"]):
            try:
                config_path, _ = find_config_path(config_name)
                if config_path:
                    config = _load_config(config_path)
                    name = config.get("name", "Unknown")
                    description = config.get("description", "No description")
                    config_port = config.get("port", "Auto")
                    route_count = len(config.get("routes", []))

                    click.echo(f"  {config_name}")
                    click.echo(f"    Name: {name}")
                    click.echo(f"    Description: {description}")
                    click.echo(f"    Port: {config_port}")
                    click.echo(f"    Routes: {route_count}")
                    click.echo()
            except Exception as e:
                click.echo(f"  {config_name} (Error loading: {e})")
                click.echo()
    else:
        click.echo("📁 Local configs (toy_api_config/apis/): None")
        click.echo()

    # Show package configs
    if configs["package"]:
        click.echo("📦 Package configs:")
        for config_name in sorted(configs["package"]):
            try:
                config_path, _ = find_config_path(config_name)
                if config_path:
                    config = _load_config(config_path)
                    name = config.get("name", "Unknown")
                    description = config.get("description", "No description")
                    config_port = config.get("port", "Auto")
                    route_count = len(config.get("routes", []))

                    click.echo(f"  {config_name}")
                    click.echo(f"    Name: {name}")
                    click.echo(f"    Description: {description}")
                    click.echo(f"    Port: {config_port}")
                    click.echo(f"    Routes: {route_count}")
                    click.echo()
            except Exception as e:
                click.echo(f"  {config_name} (Error loading: {e})")
                click.echo()
    else:
        click.echo("📦 Package configs: None found")
        click.echo()

    click.echo("Usage:")
    click.echo("  toy_api start              # Use default (v1)")
    click.echo("  toy_api start <config>     # Use specific config")
    click.echo("  toy_api init               # Create toy_api_config/")


def _list_database_configs() -> None:
    """List available database configuration files."""
    click.echo("Database Configurations:")
    click.echo()

    # Check local configs
    local_dir = Path("toy_api_config/databases")
    local_configs = []
    if local_dir.exists():
        local_configs = list(local_dir.glob("*.yaml"))

    # Check package configs
    try:
        import importlib.resources as pkg_resources
        package_dir = Path(pkg_resources.files("toy_api") / "config" / "databases")
        package_configs = list(package_dir.glob("*.yaml")) if package_dir.exists() else []
    except Exception:
        package_configs = []

    if local_configs:
        click.echo("📁 Local configs (toy_api_config/databases/):")
        for config_file in sorted(local_configs):
            click.echo(f"  {config_file.stem}")
        click.echo()
    else:
        click.echo("📁 Local configs (toy_api_config/databases/): None")
        click.echo()

    if package_configs:
        click.echo("📦 Package configs:")
        for config_file in sorted(package_configs):
            click.echo(f"  {config_file.stem}")
        click.echo()
    else:
        click.echo("📦 Package configs: None found")
        click.echo()

    click.echo("Usage:")
    click.echo("  toy_api database <config>              # Generate all tables")
    click.echo("  toy_api database <config> --tables <t> # Generate specific tables")


def _find_database_config(config_name: str) -> Optional[str]:
    """Find database configuration file by name.

    Args:
        config_name: Config name or path.

    Returns:
        Path to config file or None if not found.
    """
    # Remove .yaml extension if provided
    if config_name.endswith('.yaml'):
        config_name = config_name[:-5]

    # Check if it's a direct path
    config_path = Path(config_name)
    if config_path.exists():
        return str(config_path)

    # Add .yaml if needed
    if not str(config_path).endswith('.yaml'):
        config_path = Path(f"{config_name}.yaml")
        if config_path.exists():
            return str(config_path)

    # Check local config directory
    local_config = Path(f"toy_api_config/databases/{config_name}.yaml")
    if local_config.exists():
        return str(local_config)

    # Check package config directory
    try:
        import importlib.resources as pkg_resources
        package_config = Path(pkg_resources.files("toy_api") / "config" / "databases" / f"{config_name}.yaml")
        if package_config.exists():
            return str(package_config)
    except Exception:
        pass

    return None


def _get_all_database_configs(directory: Optional[str] = None) -> List[Tuple[str, str]]:
    """Get all database config files in a directory (including versioned subdirectories).

    Args:
        directory: Directory to search. If None, searches toy_api_config/databases/.

    Returns:
        List of (config_name, config_path) tuples.
    """
    if directory is None:
        directory = "toy_api_config/databases"

    base_path = Path(directory)
    if not base_path.exists():
        return []

    configs = []

    # Find all .yaml files recursively
    for yaml_file in base_path.rglob("*.yaml"):
        # Get relative path from base
        rel_path = yaml_file.relative_to(base_path)

        # Create config name from path (e.g., "versioned_db/1.2" or "test_db")
        if len(rel_path.parts) > 1:
            # Versioned: parent_dir/filename (without .yaml)
            config_name = str(rel_path.parent / rel_path.stem)
        else:
            # Non-versioned: just filename (without .yaml)
            config_name = rel_path.stem

        configs.append((config_name, str(yaml_file)))

    return sorted(configs)


def _generate_all_databases(
        directory: Optional[str],
        file_type: str,
        force: bool,
        partition_cols: Optional[List[str]]) -> None:
    """Generate all databases in a directory (or subdirectory).

    Args:
        directory: Directory to search (None = all databases, or specific subdirectory).
        file_type: Output file format.
        force: Overwrite existing files.
        partition_cols: Partition columns.
    """
    from toy_api.table_generator import create_table

    # Determine search directory
    if directory:
        # Check if it's a subdirectory
        subdir_path = Path(f"toy_api_config/databases/{directory}")
        if subdir_path.is_dir():
            search_dir = str(subdir_path)
        else:
            search_dir = "toy_api_config/databases"
    else:
        search_dir = "toy_api_config/databases"

    # Get all database configs
    configs = _get_all_database_configs(search_dir)

    if not configs:
        click.echo(f"No database configs found in {search_dir}")
        return

    # Filter by directory prefix if specified
    if directory:
        configs = [(name, path) for name, path in configs if name.startswith(directory)]

    if not configs:
        click.echo(f"No database configs found matching '{directory}'")
        return

    click.echo(f"Generating {len(configs)} database(s)...")
    click.echo()

    success_count = 0
    error_count = 0

    for config_name, config_path in configs:
        try:
            # Derive output path from config path structure
            config_path_obj = Path(config_path)
            parts = config_path_obj.parts
            if 'databases' in parts:
                db_index = parts.index('databases')
                db_path_parts = parts[db_index + 1:]
                db_path_parts = list(db_path_parts)
                db_path_parts[-1] = db_path_parts[-1].replace('.yaml', '')
                dest = str(Path('databases') / Path(*db_path_parts))
            else:
                dest = str(Path('databases') / config_path_obj.stem)

            click.echo(f"📊 Generating {config_name}...")

            create_table(
                table_config=config_path,
                dest=dest,
                file_type=file_type,
                partition_cols=partition_cols,
                force=force
            )

            click.echo(f"  ✓ Written to {dest}/")
            success_count += 1

        except Exception as e:
            click.echo(f"  ✗ Error: {e}", err=True)
            error_count += 1

        click.echo()

    # Summary
    click.echo(f"Summary: {success_count} succeeded, {error_count} failed")


#
# ENTRY POINT
#
def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
