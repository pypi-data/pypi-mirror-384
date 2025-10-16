"""
CLI commands for product image operations.
"""

from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.commerce import ProductImageFilters


@cli.group()
def product_images() -> None:
    """Product image management commands."""
    pass


@product_images.command()
@click.option("--product", "-p", required=True, help="Product ID")
@click.option(
    "--file",
    "-f",
    required=True,
    type=click.Path(exists=True, readable=True),
    help="Path to image file or URL",
)
@click.option("--alt", "-a", help="Alternative text for accessibility")
@click.option("--position", type=int, help="Display position (default: 1)")
@click.option(
    "--variant-ids",
    help="Comma-separated list of variant IDs this image is for",
)
@click.pass_context
def create(
    ctx: click.Context,
    product: str,
    file: str,
    alt: Optional[str],
    position: Optional[int],
    variant_ids: Optional[str],
) -> None:
    """Create a new product image."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        # Parse variant IDs if provided
        variant_id_list = []
        if variant_ids:
            variant_id_list = [vid.strip() for vid in variant_ids.split(",")]

        image_data = models.ProductImageCreate(
            product=product,
            alt=alt or "",
            position=position or 1,
            variant_ids=variant_id_list,
            file=file,
        )
        print(image_data)

        result = client.product_images.create(image_data)

        click.echo("✓ Product image created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating product image: {e}", err=True)
        ctx.exit(1)


@product_images.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--product-id", help="Filter by product ID")
@click.pass_context
def list_product_images(
    ctx: click.Context,
    page: int,
    page_size: int,
    product_id: Optional[str],
) -> None:
    """List product images."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = ProductImageFilters(
            product_id=product_id,
            ordering=None,
        )

        result = client.product_images.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No product images found.")
            return

        click.echo(f"Product images (page {page}):")
        click.echo()

        for image in result.payload:
            click.echo(image)

    except Exception as e:
        click.echo(f"✗ Error listing product images: {e}", err=True)
        ctx.exit(1)


@product_images.command()
@click.argument("image_id")
@click.pass_context
def get(ctx: click.Context, image_id: str) -> None:
    """Get a product image by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        image = client.product_images.get(image_id)

        click.echo("✓ Fetched product image successfully!")
        click.echo(image)

        click.echo("Details:")
        click.echo(image.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error getting product image: {e}", err=True)
        ctx.exit(1)


@product_images.command()
@click.argument("image_id")
@click.option("--alt", "-a", help="New alternative text")
@click.option("--position", type=int, help="New display position")
@click.option(
    "--variant-ids",
    help="New comma-separated list of variant IDs",
)
@click.pass_context
def update(
    ctx: click.Context,
    image_id: str,
    alt: Optional[str],
    position: Optional[int],
    variant_ids: Optional[str],
) -> None:
    """Update a product image."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if alt is not None:
            update_data["alt"] = alt
        if position is not None:
            update_data["position"] = position
        if variant_ids is not None:
            if variant_ids:
                update_data["variant_ids"] = [
                    vid.strip() for vid in variant_ids.split(",")
                ]
            else:
                update_data["variant_ids"] = []

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        image_update = models.ProductImageUpdate(**update_data)
        result = client.product_images.update(image_id, image_update)

        click.echo("✓ Product image updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating product image: {e}", err=True)
        ctx.exit(1)


@product_images.command()
@click.argument("image_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    image_id: str,
    yes: bool,
) -> None:
    """Delete a product image."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete product image {image_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.product_images.delete(image_id)

        click.echo(f"✓ Product image {image_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting product image: {e}", err=True)
        ctx.exit(1)
