"""
CLI commands for folder operations.
"""

from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.website import FolderFilters


@cli.group()
def folders() -> None:
    """Folder management commands."""
    pass


@folders.command()
@click.option("--name", "-n", required=True, help="Folder name")
@click.option(
    "--handle",
    "-h",
    help="URL handle",
)
@click.option("--parent-id", "-p", help="Parent folder ID")
@click.option(
    "--folder-type",
    "-t",
    default="custom",
    help="Folder type (default: custom)",
)
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    handle: str,
    parent_id: Optional[str],
    folder_type: str,
) -> None:
    """Create a new folder."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        folder_data = models.FolderCreate(
            name=name,
            handle=handle,
            parent=parent_id,
            folder_type=models.FolderType(folder_type),
        )

        result = client.folders.create(folder_data)

        click.echo("✓ Folder created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating folder: {e}", err=True)
        ctx.exit(1)


@folders.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--parent-id", help="Filter by parent folder ID")
@click.option("--folder-type", "-t", help="Filter by folder type")
@click.option("--query", "-q", help="Search query for name and handle")
@click.option("--ordering", "-o", help="Ordering field")
@click.pass_context
def list_folders(
    ctx: click.Context,
    page: int,
    page_size: int,
    parent_id: Optional[str],
    folder_type: Optional[str],
    query: Optional[str],
    ordering: Optional[str],
) -> None:
    """List folders."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = {}

        if parent_id:
            filters["parent"] = parent_id
        if folder_type:
            filters["folder_type"] = folder_type
        if query:
            filters["q"] = query
        if ordering:
            filters["ordering"] = ordering

        result = client.folders.list(
            page_size=page_size,
            page=page,
            filters=FolderFilters(**filters),
        )

        if not result.payload:
            click.echo("No folders found.")
            return

        click.echo(f"Folders (page {page}):")
        click.echo()

        for folder in result.payload:
            click.echo(folder)

    except Exception as e:
        click.echo(f"✗ Error listing folders: {e}", err=True)
        ctx.exit(1)


@folders.command()
@click.argument("folder_id")
@click.option("--name", "-n", help="New folder name")
@click.pass_context
def update(
    ctx: click.Context,
    folder_id: str,
    name: Optional[str],
) -> None:
    """Update a folder."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if name:
            update_data["name"] = name

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        folder_update = models.FolderUpdate(**update_data)
        result = client.folders.update(folder_id, folder_update)

        click.echo("✓ Folder updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating folder: {e}", err=True)
        ctx.exit(1)


@folders.command()
@click.argument("folder_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    folder_id: str,
    yes: bool,
) -> None:
    """Delete a folder."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete folder {folder_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.folders.delete(folder_id)

        click.echo(f"✓ Folder {folder_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting folder: {e}", err=True)
        ctx.exit(1)


@folders.command()
@click.argument("folder_id")
@click.pass_context
def publish(ctx: click.Context, folder_id: str) -> None:
    """Publish a folder."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.folders.publish(folder_id)

        click.echo(f"✓ Folder {folder_id} published successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error publishing folder: {e}", err=True)
        ctx.exit(1)


@folders.command()
@click.argument("folder_id")
@click.pass_context
def unpublish(ctx: click.Context, folder_id: str) -> None:
    """Unpublish a folder."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.folders.unpublish(folder_id)

        click.echo(f"✓ Folder {folder_id} unpublished successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error unpublishing folder: {e}", err=True)
        ctx.exit(1)


@folders.command("change-handle")
@click.argument("folder_id")
@click.argument("new_handle")
@click.option(
    "--redirect", "-r", is_flag=True, help="Create redirect from old handle"
)
@click.pass_context
def change_handle(
    ctx: click.Context, folder_id: str, new_handle: str, redirect: bool
) -> None:
    """Change the handle of a folder."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.folders.change_handle(folder_id, new_handle, redirect)

        click.echo(f"✓ Folder {folder_id} handle changed to '{new_handle}'!")
        if redirect:
            click.echo("✓ Redirect created from old handle.")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error changing folder handle: {e}", err=True)
        ctx.exit(1)
