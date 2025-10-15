"""
CLI commands for product operations.
"""

import json
from decimal import Decimal
from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.commerce import ProductFilters


@cli.group()
def products() -> None:
    """Product management commands."""
    pass


@products.command()
@click.option("--title", "-t", required=True, help="Product title")
@click.option(
    "--handle", "-h", help="URL handle (auto-generated if not provided)"
)
@click.option(
    "--content", "-c", help="Product content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.option(
    "--status", "-s", help="Product status (active, draft, archived)"
)
@click.option("--product-type", help="Product category or type")
@click.option("--vendor", help="Product vendor or manufacturer")
@click.option("--tags", help="Comma-separated list of product tags")
@click.option("--price", type=float, help="Product price for single variant")
@click.option(
    "--original-price", type=float, help="Original price before discount"
)
@click.pass_context
def create(
    ctx: click.Context,
    title: str,
    handle: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
    status: Optional[str],
    product_type: Optional[str],
    vendor: Optional[str],
    tags: Optional[str],
    price: Optional[float],
    original_price: Optional[float],
) -> None:
    """Create a new product."""
    # Handle content from file or direct input
    content_data = None
    if content_file:
        try:
            with open(content_file, "r", encoding="utf-8") as f:
                content_content = f.read()
            content_data = json.loads(content_content)
        except Exception as e:
            click.echo(f"Error reading content file: {e}", err=True)
            return
    elif content:
        try:
            content_data = json.loads(content)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON format for content", err=True)
            return
    else:
        content_data = {}

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        product_data = models.ProductCreate(
            title=title,
            handle=handle,
            content=content_data,
            status=(
                models.ProductStatus(status)
                if status
                else models.ProductStatus.DRAFT
            ),
            product_type=product_type or "",
            vendor=vendor or "",
            tags=tags or "",
            price=Decimal(str(price)) if price else None,
            original_price=(
                Decimal(str(original_price)) if original_price else None
            ),
        )

        result = client.products.create(product_data)

        click.echo("✓ Product created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating product: {e}", err=True)
        ctx.exit(1)


@products.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--search", "-q", help="Search in title, handle, and tags")
@click.option("--status", help="Filter by status (active, draft, archived)")
@click.option("--product-type", help="Filter by product type")
@click.option("--vendor", help="Filter by vendor name")
@click.pass_context
def list_products(
    ctx: click.Context,
    page: int,
    page_size: int,
    search: Optional[str],
    status: Optional[str],
    product_type: Optional[str],
    vendor: Optional[str],
) -> None:
    """List products."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = ProductFilters(
            q=search,
            status=status,
            product_type=product_type,
            vendor=vendor,
            ordering=None,
        )

        result = client.products.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No products found.")
            return

        click.echo(f"Products (page {page}):")
        click.echo()

        for product in result.payload:
            click.echo(product)

    except Exception as e:
        click.echo(f"✗ Error listing products: {e}", err=True)
        ctx.exit(1)


@products.command()
@click.argument("product_id")
@click.pass_context
def get(ctx: click.Context, product_id: str) -> None:
    """Get a product by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        product = client.products.get(product_id)

        click.echo("✓ Fetched product successfully!")
        click.echo(product)

        click.echo("Details:")
        click.echo(product.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error getting product: {e}", err=True)
        ctx.exit(1)


@products.command()
@click.argument("product_id")
@click.option("--title", "-t", help="New product title")
@click.option("--handle", "-h", help="New URL handle")
@click.option(
    "--content", "-c", help="New product content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.option("--status", "-s", help="New product status")
@click.option("--product-type", help="New product type")
@click.option("--vendor", help="New vendor name")
@click.option("--tags", help="New comma-separated tags")
@click.option("--currency", help="New currency code")
@click.pass_context
def update(
    ctx: click.Context,
    product_id: str,
    title: Optional[str],
    handle: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
    status: Optional[str],
    product_type: Optional[str],
    vendor: Optional[str],
    tags: Optional[str],
    currency: Optional[str],
) -> None:
    """Update a product."""
    # Handle content from file or direct input
    content_data = None
    if content_file:
        try:
            with open(content_file, "r", encoding="utf-8") as f:
                content_content = f.read()
            content_data = json.loads(content_content)
        except Exception as e:
            click.echo(f"Error reading content file: {e}", err=True)
            return
    elif content:
        try:
            content_data = json.loads(content)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON format for content", err=True)
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if title:
            update_data["title"] = title
        if handle:
            update_data["handle"] = handle
        if content_data is not None:
            update_data["content"] = content_data
        if status:
            update_data["status"] = status
        if product_type is not None:
            update_data["product_type"] = product_type
        if vendor is not None:
            update_data["vendor"] = vendor
        if tags is not None:
            update_data["tags"] = tags
        if currency:
            update_data["currency"] = currency

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        product_update = models.ProductUpdate(**update_data)
        result = client.products.update(product_id, product_update)

        click.echo("✓ Product updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating product: {e}", err=True)
        ctx.exit(1)


@products.command()
@click.argument("product_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    product_id: str,
    yes: bool,
) -> None:
    """Delete a product."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete product {product_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.products.delete(product_id)

        click.echo(f"✓ Product {product_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting product: {e}", err=True)
        ctx.exit(1)
