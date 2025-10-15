"""Command module for basic-memory project management."""

import asyncio
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from basic_memory.cli.app import app
from basic_memory.cli.commands.command_utils import get_project_info
from basic_memory.config import ConfigManager
import json
from datetime import datetime

from rich.panel import Panel
from basic_memory.mcp.async_client import get_client
from basic_memory.mcp.tools.utils import call_get
from basic_memory.schemas.project_info import ProjectList
from basic_memory.mcp.tools.utils import call_post
from basic_memory.schemas.project_info import ProjectStatusResponse
from basic_memory.mcp.tools.utils import call_delete
from basic_memory.mcp.tools.utils import call_put
from basic_memory.utils import generate_permalink
from basic_memory.mcp.tools.utils import call_patch

console = Console()

# Create a project subcommand
project_app = typer.Typer(help="Manage multiple Basic Memory projects")
app.add_typer(project_app, name="project")


def format_path(path: str) -> str:
    """Format a path for display, using ~ for home directory."""
    home = str(Path.home())
    if path.startswith(home):
        return path.replace(home, "~", 1)  # pragma: no cover
    return path


@project_app.command("list")
def list_projects() -> None:
    """List all Basic Memory projects."""

    async def _list_projects():
        async with get_client() as client:
            response = await call_get(client, "/projects/projects")
            return ProjectList.model_validate(response.json())

    try:
        result = asyncio.run(_list_projects())

        table = Table(title="Basic Memory Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Default", style="magenta")

        for project in result.projects:
            is_default = "✓" if project.is_default else ""
            table.add_row(project.name, format_path(project.path), is_default)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing projects: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("add")
def add_project(
    name: str = typer.Argument(..., help="Name of the project"),
    path: str = typer.Argument(
        None, help="Path to the project directory (required for local mode)"
    ),
    set_default: bool = typer.Option(False, "--default", help="Set as default project"),
) -> None:
    """Add a new project.

    For cloud mode: only name is required
    For local mode: both name and path are required
    """
    config = ConfigManager().config

    if config.cloud_mode_enabled:
        # Cloud mode: path not needed (auto-generated from name)
        async def _add_project():
            async with get_client() as client:
                data = {"name": name, "path": generate_permalink(name), "set_default": set_default}
                response = await call_post(client, "/projects/projects", json=data)
                return ProjectStatusResponse.model_validate(response.json())
    else:
        # Local mode: path is required
        if path is None:
            console.print("[red]Error: path argument is required in local mode[/red]")
            raise typer.Exit(1)

        # Resolve to absolute path
        resolved_path = Path(os.path.abspath(os.path.expanduser(path))).as_posix()

        async def _add_project():
            async with get_client() as client:
                data = {"name": name, "path": resolved_path, "set_default": set_default}
                response = await call_post(client, "/projects/projects", json=data)
                return ProjectStatusResponse.model_validate(response.json())

    try:
        result = asyncio.run(_add_project())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:
        console.print(f"[red]Error adding project: {str(e)}[/red]")
        raise typer.Exit(1)

    # Display usage hint
    console.print("\nTo use this project:")
    console.print(f"  basic-memory --project={name} <command>")


@project_app.command("remove")
def remove_project(
    name: str = typer.Argument(..., help="Name of the project to remove"),
) -> None:
    """Remove a project."""

    async def _remove_project():
        async with get_client() as client:
            project_permalink = generate_permalink(name)
            response = await call_delete(client, f"/projects/{project_permalink}")
            return ProjectStatusResponse.model_validate(response.json())

    try:
        result = asyncio.run(_remove_project())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:
        console.print(f"[red]Error removing project: {str(e)}[/red]")
        raise typer.Exit(1)

    # Show this message regardless of method used
    console.print("[yellow]Note: The project files have not been deleted from disk.[/yellow]")


@project_app.command("default")
def set_default_project(
    name: str = typer.Argument(..., help="Name of the project to set as CLI default"),
) -> None:
    """Set the default project when 'config.default_project_mode' is set.

    Note: This command is only available in local mode.
    """
    config = ConfigManager().config

    if config.cloud_mode_enabled:
        console.print("[red]Error: 'default' command is not available in cloud mode[/red]")
        raise typer.Exit(1)

    async def _set_default():
        async with get_client() as client:
            project_permalink = generate_permalink(name)
            response = await call_put(client, f"/projects/{project_permalink}/default")
            return ProjectStatusResponse.model_validate(response.json())

    try:
        result = asyncio.run(_set_default())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:
        console.print(f"[red]Error setting default project: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("sync-config")
def synchronize_projects() -> None:
    """Synchronize project config between configuration file and database.

    Note: This command is only available in local mode.
    """
    config = ConfigManager().config

    if config.cloud_mode_enabled:
        console.print("[red]Error: 'sync-config' command is not available in cloud mode[/red]")
        raise typer.Exit(1)

    async def _sync_config():
        async with get_client() as client:
            response = await call_post(client, "/projects/config/sync")
            return ProjectStatusResponse.model_validate(response.json())

    try:
        result = asyncio.run(_sync_config())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:  # pragma: no cover
        console.print(f"[red]Error synchronizing projects: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("move")
def move_project(
    name: str = typer.Argument(..., help="Name of the project to move"),
    new_path: str = typer.Argument(..., help="New absolute path for the project"),
) -> None:
    """Move a project to a new location.

    Note: This command is only available in local mode.
    """
    config = ConfigManager().config

    if config.cloud_mode_enabled:
        console.print("[red]Error: 'move' command is not available in cloud mode[/red]")
        raise typer.Exit(1)

    # Resolve to absolute path
    resolved_path = Path(os.path.abspath(os.path.expanduser(new_path))).as_posix()

    async def _move_project():
        async with get_client() as client:
            data = {"path": resolved_path}
            project_permalink = generate_permalink(name)

            # TODO fix route to use ProjectPathDep
            response = await call_patch(client, f"/{name}/project/{project_permalink}", json=data)
            return ProjectStatusResponse.model_validate(response.json())

    try:
        result = asyncio.run(_move_project())
        console.print(f"[green]{result.message}[/green]")

        # Show important file movement reminder
        console.print()  # Empty line for spacing
        console.print(
            Panel(
                "[bold red]IMPORTANT:[/bold red] Project configuration updated successfully.\n\n"
                "[yellow]You must manually move your project files from the old location to:[/yellow]\n"
                f"[cyan]{resolved_path}[/cyan]\n\n"
                "[dim]Basic Memory has only updated the configuration - your files remain in their original location.[/dim]",
                title="⚠️  Manual File Movement Required",
                border_style="yellow",
                expand=False,
            )
        )

    except Exception as e:
        console.print(f"[red]Error moving project: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("info")
def display_project_info(
    name: str = typer.Argument(..., help="Name of the project"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display detailed information and statistics about the current project."""
    try:
        # Get project info
        info = asyncio.run(get_project_info(name))

        if json_output:
            # Convert to JSON and print
            print(json.dumps(info.model_dump(), indent=2, default=str))
        else:
            # Project configuration section
            console.print(
                Panel(
                    f"Basic Memory version: [bold green]{info.system.version}[/bold green]\n"
                    f"[bold]Project:[/bold] {info.project_name}\n"
                    f"[bold]Path:[/bold] {info.project_path}\n"
                    f"[bold]Default Project:[/bold] {info.default_project}\n",
                    title="📊 Basic Memory Project Info",
                    expand=False,
                )
            )

            # Statistics section
            stats_table = Table(title="📈 Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Count", style="green")

            stats_table.add_row("Entities", str(info.statistics.total_entities))
            stats_table.add_row("Observations", str(info.statistics.total_observations))
            stats_table.add_row("Relations", str(info.statistics.total_relations))
            stats_table.add_row(
                "Unresolved Relations", str(info.statistics.total_unresolved_relations)
            )
            stats_table.add_row("Isolated Entities", str(info.statistics.isolated_entities))

            console.print(stats_table)

            # Entity types
            if info.statistics.entity_types:
                entity_types_table = Table(title="📑 Entity Types")
                entity_types_table.add_column("Type", style="blue")
                entity_types_table.add_column("Count", style="green")

                for entity_type, count in info.statistics.entity_types.items():
                    entity_types_table.add_row(entity_type, str(count))

                console.print(entity_types_table)

            # Most connected entities
            if info.statistics.most_connected_entities:  # pragma: no cover
                connected_table = Table(title="🔗 Most Connected Entities")
                connected_table.add_column("Title", style="blue")
                connected_table.add_column("Permalink", style="cyan")
                connected_table.add_column("Relations", style="green")

                for entity in info.statistics.most_connected_entities:
                    connected_table.add_row(
                        entity["title"], entity["permalink"], str(entity["relation_count"])
                    )

                console.print(connected_table)

            # Recent activity
            if info.activity.recently_updated:  # pragma: no cover
                recent_table = Table(title="🕒 Recent Activity")
                recent_table.add_column("Title", style="blue")
                recent_table.add_column("Type", style="cyan")
                recent_table.add_column("Last Updated", style="green")

                for entity in info.activity.recently_updated[:5]:  # Show top 5
                    updated_at = (
                        datetime.fromisoformat(entity["updated_at"])
                        if isinstance(entity["updated_at"], str)
                        else entity["updated_at"]
                    )
                    recent_table.add_row(
                        entity["title"],
                        entity["entity_type"],
                        updated_at.strftime("%Y-%m-%d %H:%M"),
                    )

                console.print(recent_table)

            # Available projects
            projects_table = Table(title="📁 Available Projects")
            projects_table.add_column("Name", style="blue")
            projects_table.add_column("Path", style="cyan")
            projects_table.add_column("Default", style="green")

            for name, proj_info in info.available_projects.items():
                is_default = name == info.default_project
                project_path = proj_info["path"]
                projects_table.add_row(name, project_path, "✓" if is_default else "")

            console.print(projects_table)

            # Timestamp
            current_time = (
                datetime.fromisoformat(str(info.system.timestamp))
                if isinstance(info.system.timestamp, str)
                else info.system.timestamp
            )
            console.print(f"\nTimestamp: [cyan]{current_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")

    except Exception as e:  # pragma: no cover
        typer.echo(f"Error getting project info: {e}", err=True)
        raise typer.Exit(1)
