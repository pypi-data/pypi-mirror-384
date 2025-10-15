"""Upload CLI commands for basic-memory projects."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from basic_memory.cli.app import cloud_app
from basic_memory.cli.commands.cloud.cloud_utils import (
    create_cloud_project,
    project_exists,
    sync_project,
)
from basic_memory.cli.commands.cloud.upload import upload_path

console = Console()


@cloud_app.command("upload")
def upload(
    path: Path = typer.Argument(
        ...,
        help="Path to local file or directory to upload",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    project: str = typer.Option(
        ...,
        "--project",
        "-p",
        help="Cloud project name (destination)",
    ),
    create_project: bool = typer.Option(
        False,
        "--create-project",
        "-c",
        help="Create project if it doesn't exist",
    ),
    sync: bool = typer.Option(
        True,
        "--sync/--no-sync",
        help="Sync project after upload (default: true)",
    ),
) -> None:
    """Upload local files or directories to cloud project via WebDAV.

    Examples:
      bm cloud upload ~/my-notes --project research
      bm cloud upload notes.md --project research --create-project
      bm cloud upload ~/docs --project work --no-sync
    """

    async def _upload():
        # Check if project exists
        if not await project_exists(project):
            if create_project:
                console.print(f"[blue]Creating cloud project '{project}'...[/blue]")
                try:
                    await create_cloud_project(project)
                    console.print(f"[green]✓ Created project '{project}'[/green]")
                except Exception as e:
                    console.print(f"[red]Failed to create project: {e}[/red]")
                    raise typer.Exit(1)
            else:
                console.print(
                    f"[red]Project '{project}' does not exist.[/red]\n"
                    f"[yellow]Options:[/yellow]\n"
                    f"  1. Create it first: bm project add {project}\n"
                    f"  2. Use --create-project flag to create automatically"
                )
                raise typer.Exit(1)

        # Perform upload
        console.print(f"[blue]Uploading {path} to project '{project}'...[/blue]")
        success = await upload_path(path, project)
        if not success:
            console.print("[red]Upload failed[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✅ Successfully uploaded to '{project}'[/green]")

        # Sync project if requested
        if sync:
            console.print(f"[blue]Syncing project '{project}'...[/blue]")
            try:
                await sync_project(project)
            except Exception as e:
                console.print(f"[yellow]Warning: Sync failed: {e}[/yellow]")
                console.print("[dim]Files uploaded but may not be indexed yet[/dim]")

    asyncio.run(_upload())
