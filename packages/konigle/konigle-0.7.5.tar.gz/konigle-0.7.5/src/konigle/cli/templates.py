"""CLI commands for template management."""

import json
from typing import Optional

import click

from konigle.cli.main import cli, get_client
from konigle.filters.website import TemplateFilters
from konigle.models.website.template import TemplateCreate, TemplateUpdate


@cli.group()
def templates():
    """Manage templates for landing pages."""
    pass


@templates.command()
@click.option("--name", required=True, help="Name of the template")
@click.option("--handle", required=True, help="Handle for the template")
@click.option("--layout", help="Layout configuration as JSON string")
@click.option(
    "--layout-file",
    type=click.Path(exists=True, readable=True),
    help="Path to JSON layout file",
)
@click.option("--is-base", is_flag=True, help="Mark as base template")
@click.option("--base", help="Base template ID to extend")
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    handle: str,
    layout: Optional[str],
    layout_file: Optional[str],
    is_base: bool,
    base: Optional[str],
):
    """Create a new template."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    # Handle layout from file or direct input
    layout_dict = None
    if layout_file:
        try:
            with open(layout_file, "r", encoding="utf-8") as f:
                layout_content = f.read()
            layout_dict = json.loads(layout_content)
        except Exception as e:
            click.echo(f"Error reading layout file: {e}", err=True)
            return
    elif layout:
        try:
            layout_dict = json.loads(layout)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON format for layout", err=True)
            return

    try:
        template_data = TemplateCreate(
            name=name,
            handle=handle,
            layout=layout_dict,
            is_base=is_base,
            base=base,
        )
        template = client.templates.create(template_data)
        click.echo("✅ Created template successfully")
        click.echo(template)

    except Exception as e:
        click.echo(f"Error creating template: {e}", err=True)


@templates.command("list")
@click.option("--query", help="Search query for name and handle")
@click.option("--handle", help="Filter by template handle")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.pass_context
def list_templates(
    ctx: click.Context,
    query: Optional[str],
    handle: Optional[str],
    page: int,
    page_size: int,
):
    """List templates."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        filters = TemplateFilters(
            q=query,
            handle=handle,
        )
        templates = client.templates.list(
            page=page, page_size=page_size, filters=filters
        )

        if not templates.payload:
            click.echo("No templates found.")
            return

        for template in templates.payload:
            click.echo(template)

        click.echo(
            f"Page {templates.current_page} of {templates.num_pages} "
            f"(Total: {templates.count})"
        )

    except Exception as e:
        click.echo(f"Error listing templates: {e}", err=True)


@templates.command()
@click.argument("template_id")
@click.pass_context
def get(ctx: click.Context, template_id: str):
    """Get a template by ID."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        template = client.templates.get(template_id)
        click.echo("✅ Fetched template successfully")
        click.echo(template)
        click.echo("Details:")
        click.echo("Layout:")
        click.echo("-" * 20)
        if template.layout:
            click.echo(template.layout.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"Error getting template: {e}", err=True)


@templates.command()
@click.argument("template_id")
@click.option("--name", help="New name for the template")
@click.option("--handle", help="New handle for the template")
@click.option("--layout", help="New layout configuration as JSON string")
@click.option(
    "--layout-file",
    type=click.Path(exists=True, readable=True),
    help="Path to new JSON layout file",
)
@click.option("--is-base", type=bool, help="Update base template status")
@click.option("--base", help="New base template ID")
@click.pass_context
def update(
    ctx: click.Context,
    template_id: str,
    name: Optional[str],
    handle: Optional[str],
    layout: Optional[str],
    layout_file: Optional[str],
    is_base: Optional[bool],
    base: Optional[str],
):
    """Update a template."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    # Handle layout from file or direct input
    layout_dict = None
    if layout_file:
        try:
            with open(layout_file, "r", encoding="utf-8") as f:
                layout_content = f.read()
            layout_dict = json.loads(layout_content)
        except Exception as e:
            click.echo(f"Error reading layout file: {e}", err=True)
            return
    elif layout:
        try:
            layout_dict = json.loads(layout)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON format for layout", err=True)
            return

    try:
        update_data = TemplateUpdate(
            name=name,
            handle=handle,
            layout=layout_dict,
            is_base=is_base,
            base=base,
        )
        template = client.templates.update(template_id, update_data)
        click.echo("✅ Updated template successfully")
        click.echo(template)

    except Exception as e:
        click.echo(f"Error updating template: {e}", err=True)


@templates.command()
@click.argument("template_id")
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.pass_context
def delete(ctx: click.Context, template_id: str, confirm: bool):
    """Delete a template."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    if not confirm:
        if not click.confirm(f"Delete template {template_id}?"):
            return

    try:
        client.templates.delete(template_id)
        click.echo(f"Deleted template: {template_id}")

    except Exception as e:
        click.echo(f"Error deleting template: {e}", err=True)


if __name__ == "__main__":
    templates()
