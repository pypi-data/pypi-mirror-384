"""CLI commands for component management."""

from typing import Literal, Optional

import click

from konigle.cli.main import cli, get_client
from konigle.filters.website import ComponentFilters
from konigle.models.website.component import ComponentCreate, ComponentUpdate


@cli.group()
def components():
    """Manage components for landing pages."""
    pass


@components.command()
@click.option("--name", required=True, help="Name of the component")
@click.option("--description", default="", help="Description of the component")
@click.option(
    "--type",
    "component_type",
    default="component",
    type=click.Choice(["component", "widget"]),
    help="Type of component",
)
@click.option("--version", default="1.0.0", help="Version of the component")
@click.option(
    "--template-html", help="Django template HTML content or file path"
)
@click.option(
    "--template-file",
    type=click.Path(exists=True, readable=True),
    help="Path to HTML template file",
)
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    description: str,
    component_type: Literal["component", "widget"],
    version: str,
    template_html: Optional[str],
    template_file: Optional[str],
):
    """Create a new component."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    # make sure either template_html or template_file is provided
    if not template_html and not template_file:
        click.echo(
            "Error: Either --template-html or --template-file must be provided",
            err=True,
        )
        return

    # Handle template HTML from file or direct input
    html_content = ""
    if template_file:
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            click.echo(f"Error reading template file: {e}", err=True)
            return
    elif template_html:
        html_content = template_html

    try:
        component_data = ComponentCreate(
            name=name,
            description=description,
            version=version,
            template_html=html_content,
        )
        component = client.components.create(
            component_data, type_=component_type
        )
        click.echo("✅ Created component successfully")
        click.echo(component)

    except Exception as e:
        click.echo(f"Error creating component: {e}", err=True)


@components.command("list")
@click.option("--query", help="Search query for name and description")
@click.option(
    "--type",
    "component_type",
    help="Filter by component type. Use comma to separate multiple types",
)
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.pass_context
def list_components(
    ctx: click.Context,
    query: Optional[str],
    component_type: Optional[str],
    page: int,
    page_size: int,
):
    """List components."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        filters = ComponentFilters(
            q=query,
            type=component_type,
        )
        components = client.components.list(
            page=page, page_size=page_size, filters=filters
        )

        if not components.payload:
            click.echo("No components found.")
            return

        for component in components.payload:
            click.echo(component)

        # Show pagination info
        click.echo(
            f"Page {components.current_page} of {components.num_pages} "
            f"(Total: {components.count})"
        )

    except Exception as e:
        click.echo(f"Error listing components: {e}", err=True)


@components.command()
@click.argument("component_id")
@click.pass_context
def get(ctx: click.Context, component_id: str):
    """Get a component by ID."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        component = client.components.get(component_id)
        click.echo("✅ Fetched component successfully")
        click.echo(component)
        click.echo("Details:")

        click.echo("HTML Template:")
        click.echo("-" * 20)
        click.echo(component.template_html)

    except Exception as e:
        click.echo(f"Error getting component: {e}", err=True)


@components.command()
@click.argument("component_id")
@click.option("--name", help="New name for the component")
@click.option("--description", help="New description for the component")
@click.option("--version", help="New version for the component")
@click.option("--template-html", help="New Django template HTML content")
@click.option(
    "--template-file",
    type=click.Path(exists=True, readable=True),
    help="Path to new HTML template file",
)
@click.pass_context
def update(
    ctx: click.Context,
    component_id: str,
    name: Optional[str],
    description: Optional[str],
    version: Optional[str],
    template_html: Optional[str],
    template_file: Optional[str],
):
    """Update a component."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    # Handle template HTML from file or direct input
    html_content = None
    if template_file:
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            click.echo(f"Error reading template file: {e}", err=True)
            return
    elif template_html:
        html_content = template_html

    try:
        update_data = ComponentUpdate(
            name=name,
            description=description,
            version=version,
            template_html=html_content,
        )
        component = client.components.update(component_id, update_data)
        click.echo("✅ Updated component successfully")
        click.echo(component)

    except Exception as e:
        click.echo(f"Error updating component: {e}", err=True)


@components.command()
@click.argument("component_id")
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.pass_context
def delete(ctx: click.Context, component_id: str, confirm: bool):
    """Delete a component."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    if not confirm:
        if not click.confirm(f"Delete component {component_id}?"):
            return

    try:
        client.components.delete(component_id)
        click.echo(f"Deleted component: {component_id}")

    except Exception as e:
        click.echo(f"Error deleting component: {e}", err=True)


if __name__ == "__main__":
    components()
