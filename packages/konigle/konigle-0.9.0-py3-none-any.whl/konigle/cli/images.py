"""
CLI commands for image operations.
"""

from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client


@cli.group()
def images() -> None:
    """Image management commands."""
    pass


@images.command()
@click.option("--file", "-f", required=True, help="Path to image file or URL")
@click.option("--name", "-n", required=True, help="Image name")
@click.option("--alt-text", "-a", help="Alt text for the image")
@click.option("--tags", "-t", help="Comma-separated tags")
@click.pass_context
def create(
    ctx: click.Context,
    file: str,
    name: str,
    alt_text: Optional[str],
    tags: Optional[str],
) -> None:
    """Create a new image."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        image_data = models.ImageCreate(
            name=name,
            alt_text=alt_text or f"Image: {name}",
            tags=tags or "",
            image=file,
        )

        result = client.images.create(image_data)

        click.echo("✓ Image created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating image: {e}", err=True)
        ctx.exit(1)


@images.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--ordering", "-o", help="Ordering field")
@click.pass_context
def list_images(
    ctx: click.Context,
    page: int,
    page_size: int,
    ordering: Optional[str],
) -> None:
    """List images."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        result = client.images.list(
            page=page,
            page_size=page_size,
            ordering=ordering,
        )

        if not result.payload:
            click.echo("No images found.")
            return

        click.echo(f"Images (page {page}):")
        click.echo()

        for image in result.payload:
            click.echo(image)

    except Exception as e:
        click.echo(f"✗ Error listing images: {e}", err=True)
        ctx.exit(1)


@images.command()
@click.argument("image_id")
@click.option("--name", "-n", help="New image name")
@click.option("--alt-text", "-a", help="New alt text")
@click.option("--tags", "-t", help="New comma-separated tags")
@click.pass_context
def update(
    ctx: click.Context,
    image_id: str,
    name: Optional[str],
    alt_text: Optional[str],
    tags: Optional[str],
) -> None:
    """Update an image."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        # Build update data with only provided fields
        update_data = {}
        if name:
            update_data["name"] = name
        if alt_text:
            update_data["alt_text"] = alt_text
        if tags is not None:
            update_data["tags"] = [
                tag.strip() for tag in tags.split(",") if tag.strip()
            ]

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        image_update = models.ImageUpdate(**update_data)
        result = client.images.update(image_id, image_update)

        click.echo("✓ Image updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating image: {e}", err=True)
        ctx.exit(1)


@images.command()
@click.argument("image_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    image_id: str,
    yes: bool,
) -> None:
    """Delete an image."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete image {image_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.images.delete(image_id)

        click.echo(f"✓ Image {image_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting image: {e}", err=True)
        ctx.exit(1)
