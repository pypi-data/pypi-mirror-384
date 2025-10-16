"""
CLI commands for product variant operations.
"""

import json
from decimal import Decimal
from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.commerce import ProductVariantFilters


@cli.group()
def product_variants() -> None:
    """Product variant management commands."""
    pass


@product_variants.command()
@click.option("--product", "-p", required=True, help="Product ID")
@click.option("--title", "-t", help="Variant title")
@click.option("--price", type=float, required=True, help="Variant price")
@click.option("--sku", help="Stock Keeping Unit identifier")
@click.option("--barcode", help="Product barcode or UPC")
@click.option("--compare-at-price", type=float, help="Original price before discount")
@click.option("--cost", type=float, help="Cost of goods sold")
@click.option("--currency", help="Currency code (e.g., USD, EUR)")
@click.option("--option1", help="First product option value (e.g., Size)")
@click.option("--option2", help="Second product option value (e.g., Color)")
@click.option("--option3", help="Third product option value (e.g., Material)")
@click.option("--position", type=int, help="Display position (default: 1)")
@click.option("--weight", type=float, help="Variant weight for shipping")
@click.option("--weight-unit", help="Unit of measurement for weight")
@click.option("--grams", type=int, help="Weight in grams")
@click.option("--taxable/--no-taxable", default=True, help="Whether variant is taxable")
@click.option("--inventory-policy", default="deny", help="Inventory policy")
@click.option("--inventory-quantity", type=int, default=1, help="Stock quantity")
@click.option("--image", help="ID of the variant image")
@click.option(
    "--content", "-c", help="Variant content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.pass_context
def create(
    ctx: click.Context,
    product: str,
    title: Optional[str],
    price: float,
    sku: Optional[str],
    barcode: Optional[str],
    compare_at_price: Optional[float],
    cost: Optional[float],
    currency: Optional[str],
    option1: Optional[str],
    option2: Optional[str],
    option3: Optional[str],
    position: Optional[int],
    weight: Optional[float],
    weight_unit: Optional[str],
    grams: Optional[int],
    taxable: bool,
    inventory_policy: str,
    inventory_quantity: int,
    image: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
) -> None:
    """Create a new product variant."""
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

        variant_data = models.ProductVariantCreate(
            title=title,
            price=Decimal(str(price)),
            sku=sku,
            barcode=barcode,
            compare_at_price=Decimal(str(compare_at_price)) if compare_at_price else None,
            cost=Decimal(str(cost)) if cost else None,
            currency=currency,
            option1=option1,
            option2=option2,
            option3=option3,
            position=position or 1,
            weight=weight,
            weight_unit=weight_unit,
            grams=grams,
            taxable=taxable,
            inventory_policy=inventory_policy,
            inventory_quantity=inventory_quantity,
            image=image,
            content=content_data,
        )

        result = client.product_variants.create(variant_data)

        click.echo("✓ Product variant created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating product variant: {e}", err=True)
        ctx.exit(1)


@product_variants.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--search", "-q", help="Search in title, sku, and barcode")
@click.option("--product-id", help="Filter by product ID")
@click.pass_context
def list_product_variants(
    ctx: click.Context,
    page: int,
    page_size: int,
    search: Optional[str],
    product_id: Optional[str],
) -> None:
    """List product variants."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = ProductVariantFilters(
            q=search,
            product_id=product_id,
            ordering=None,
        )

        result = client.product_variants.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No product variants found.")
            return

        click.echo(f"Product variants (page {page}):")
        click.echo()

        for variant in result.payload:
            click.echo(variant)

    except Exception as e:
        click.echo(f"✗ Error listing product variants: {e}", err=True)
        ctx.exit(1)


@product_variants.command()
@click.argument("variant_id")
@click.pass_context
def get(ctx: click.Context, variant_id: str) -> None:
    """Get a product variant by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        variant = client.product_variants.get(variant_id)

        click.echo("✓ Fetched product variant successfully!")
        click.echo(variant)

        click.echo("Details:")
        click.echo(variant.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error getting product variant: {e}", err=True)
        ctx.exit(1)


@product_variants.command()
@click.argument("variant_id")
@click.option("--title", "-t", help="New variant title")
@click.option("--handle", "-h", help="New URL handle")
@click.option("--price", type=float, help="New variant price")
@click.option("--sku", help="New SKU")
@click.option("--barcode", help="New barcode")
@click.option("--compare-at-price", type=float, help="New compare at price")
@click.option("--cost", type=float, help="New cost")
@click.option("--currency", help="New currency code")
@click.option("--position", type=int, help="New display position")
@click.option("--weight", type=float, help="New weight")
@click.option("--weight-unit", help="New weight unit")
@click.option("--grams", type=int, help="New weight in grams")
@click.option("--taxable/--no-taxable", help="Whether variant is taxable")
@click.option("--inventory-policy", help="New inventory policy")
@click.option("--inventory-quantity", type=int, help="New stock quantity")
@click.option("--image", help="New variant image ID")
@click.option(
    "--content", "-c", help="New variant content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.pass_context
def update(
    ctx: click.Context,
    variant_id: str,
    title: Optional[str],
    handle: Optional[str],
    price: Optional[float],
    sku: Optional[str],
    barcode: Optional[str],
    compare_at_price: Optional[float],
    cost: Optional[float],
    currency: Optional[str],
    position: Optional[int],
    weight: Optional[float],
    weight_unit: Optional[str],
    grams: Optional[int],
    taxable: Optional[bool],
    inventory_policy: Optional[str],
    inventory_quantity: Optional[int],
    image: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
) -> None:
    """Update a product variant."""
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
        if price is not None:
            update_data["price"] = Decimal(str(price))
        if sku is not None:
            update_data["sku"] = sku
        if barcode is not None:
            update_data["barcode"] = barcode
        if compare_at_price is not None:
            update_data["compare_at_price"] = Decimal(str(compare_at_price))
        if cost is not None:
            update_data["cost"] = Decimal(str(cost))
        if currency:
            update_data["currency"] = currency
        if position is not None:
            update_data["position"] = position
        if weight is not None:
            update_data["weight"] = weight
        if weight_unit is not None:
            update_data["weight_unit"] = weight_unit
        if grams is not None:
            update_data["grams"] = grams
        if taxable is not None:
            update_data["taxable"] = taxable
        if inventory_policy:
            update_data["inventory_policy"] = inventory_policy
        if inventory_quantity is not None:
            update_data["inventory_quantity"] = inventory_quantity
        if image is not None:
            update_data["image"] = image
        if content_data is not None:
            update_data["content"] = content_data

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        variant_update = models.ProductVariantUpdate(**update_data)
        result = client.product_variants.update(variant_id, variant_update)

        click.echo("✓ Product variant updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating product variant: {e}", err=True)
        ctx.exit(1)


@product_variants.command()
@click.argument("variant_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    variant_id: str,
    yes: bool,
) -> None:
    """Delete a product variant."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete product variant {variant_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.product_variants.delete(variant_id)

        click.echo(f"✓ Product variant {variant_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting product variant: {e}", err=True)
        ctx.exit(1)