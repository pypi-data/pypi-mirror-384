"""
CLI commands for glossary term operations.
"""

import json
from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.website import GlossaryTermFilters


@cli.group()
def glossary() -> None:
    """Glossary term management commands."""
    pass


@glossary.command()
@click.option("--title", "-t", required=True, help="Glossary term title")
@click.option(
    "--name", "-n", help="Term name (defaults to title if not provided)"
)
@click.option(
    "--handle", "-h", help="URL handle (auto-generated if not provided)"
)
@click.option("--content", "-c", help="Term content as EditorJS JSON string")
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.option("--summary", "-s", help="Term summary")
@click.option("--author", "-a", help="Author ID")
@click.pass_context
def create(
    ctx: click.Context,
    title: str,
    name: Optional[str],
    handle: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
    summary: Optional[str],
    author: Optional[str],
) -> None:
    """Create a new glossary term."""
    name = name or title

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

        term_data = models.GlossaryTermCreate(
            title=title,
            name=name,
            handle=handle,
            content=content_data,
            summary=summary or "",
            author=author,
        )

        result = client.glossary_terms.create(term_data)

        click.echo("✓ Glossary term created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating glossary term: {e}", err=True)
        ctx.exit(1)


@glossary.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--published", is_flag=True, help="Filter by published status")
@click.pass_context
def list_terms(
    ctx: click.Context,
    page: int,
    page_size: int,
    published: Optional[bool],
) -> None:
    """List glossary terms."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = GlossaryTermFilters(
            published=published,
        )

        result = client.glossary_terms.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No glossary terms found.")
            return

        click.echo(f"Glossary terms (page {page}):")
        click.echo()

        for term in result.payload:
            click.echo(term)

    except Exception as e:
        click.echo(f"✗ Error listing glossary terms: {e}", err=True)
        ctx.exit(1)


@glossary.command()
@click.argument("term_id")
@click.pass_context
def get(ctx: click.Context, term_id: str) -> None:
    """Get a glossary term by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        term = client.glossary_terms.get(term_id)

        click.echo("✓ Fetched glossary term successfully!")
        click.echo(term)

        click.echo("Details:")
        click.echo(term.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error getting glossary term: {e}", err=True)
        ctx.exit(1)


@glossary.command()
@click.argument("term_id")
@click.option("--title", "-t", help="New glossary term title")
@click.option("--name", "-n", help="New term name")
@click.option(
    "--content", "-c", help="New term content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.option("--summary", "-s", help="New term summary")
@click.option("--json-ld", "-j", help="JSON-LD structured data as JSON string")
@click.option("--seo", "-m", help="SEO meta as JSON string")
@click.pass_context
def update(
    ctx: click.Context,
    term_id: str,
    title: Optional[str],
    name: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
    summary: Optional[str],
    json_ld: Optional[str],
    seo: Optional[str],
) -> None:
    """Update a glossary term."""
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
        if name:
            update_data["name"] = name
        if content_data is not None:
            update_data["content"] = content_data
        if summary is not None:
            update_data["summary"] = summary
        if json_ld:
            try:
                update_data["json_ld"] = json.loads(json_ld)
            except json.JSONDecodeError:
                click.echo("Error: Invalid JSON format for JSON-LD", err=True)
                return
        if seo:
            try:
                update_data["seo_meta"] = json.loads(seo)
            except json.JSONDecodeError:
                click.echo("Error: Invalid JSON format for SEO meta", err=True)
                return

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        term_update = models.GlossaryTermUpdate(**update_data)
        result = client.glossary_terms.update(term_id, term_update)

        click.echo("✓ Glossary term updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating glossary term: {e}", err=True)
        ctx.exit(1)


@glossary.command()
@click.argument("term_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    term_id: str,
    yes: bool,
) -> None:
    """Delete a glossary term."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete glossary term {term_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.glossary_terms.delete(term_id)

        click.echo(f"✓ Glossary term {term_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting glossary term: {e}", err=True)
        ctx.exit(1)


@glossary.command()
@click.argument("term_id")
@click.pass_context
def publish(ctx: click.Context, term_id: str) -> None:
    """Publish a glossary term."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.glossary_terms.publish(term_id)

        click.echo(f"✓ Glossary term {term_id} published successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error publishing glossary term: {e}", err=True)
        ctx.exit(1)


@glossary.command()
@click.argument("term_id")
@click.pass_context
def unpublish(ctx: click.Context, term_id: str) -> None:
    """Unpublish a glossary term."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.glossary_terms.unpublish(term_id)

        click.echo(f"✓ Glossary term {term_id} unpublished successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error unpublishing glossary term: {e}", err=True)
        ctx.exit(1)


@glossary.command("change-handle")
@click.argument("term_id")
@click.argument("new_handle")
@click.option(
    "--redirect", "-r", is_flag=True, help="Create redirect from old handle"
)
@click.pass_context
def change_handle(
    ctx: click.Context, term_id: str, new_handle: str, redirect: bool
) -> None:
    """Change the handle of a glossary term."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.glossary_terms.change_handle(term_id, new_handle, redirect)

        click.echo(f"✓ Glossary term {term_id} handle changed to '{new_handle}'!")
        if redirect:
            click.echo("✓ Redirect created from old handle.")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error changing glossary term handle: {e}", err=True)
        ctx.exit(1)
