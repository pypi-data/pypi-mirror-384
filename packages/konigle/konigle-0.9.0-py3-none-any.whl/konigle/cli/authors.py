"""CLI commands for author management."""

import json
from typing import Optional

import click

from konigle.cli.main import cli, get_client
from konigle.filters.website import AuthorFilters
from konigle.models.website.author import CreateAuthor, UpdateAuthor


@cli.group()
def authors():
    """Manage content authors."""
    pass


@authors.command()
@click.option("--name", required=True, help="Name of the author")
@click.option("--handle", required=True, help="URL handle for the author")
@click.option("--tagline", help="Author tagline (e.g., Marketing Head)")
@click.option("--bio", help="Brief bio of the author")
@click.option("--email", help="Email address of the author")
@click.option("--avatar", help="Path to avatar image file")
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    handle: str,
    tagline: Optional[str],
    bio: Optional[str],
    email: Optional[str],
    avatar: Optional[str],
):
    """Create a new author."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        author_data = CreateAuthor(
            name=name,
            handle=handle,
            tagline=tagline or "",
            bio=bio or "",
            email=email or "",
            avatar=avatar,
        )
        author = client.authors.create(author_data)
        click.echo("✓ Author created successfully!")
        click.echo(author)

    except Exception as e:
        import traceback

        traceback.print_exc()
        click.echo(f"Error creating author: {e}", err=True)


@authors.command("list")
@click.option("--query", help="Search query for name and handle")
@click.option("--handle", help="Filter by author handle")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.pass_context
def list_authors(
    ctx: click.Context,
    query: Optional[str],
    handle: Optional[str],
    page: int,
    page_size: int,
):
    """List authors."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        filters = AuthorFilters(
            q=query,
            handle=handle,
        )

        result = client.authors.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No authors found.")
            return

        click.echo(f"Authors (page {page}):")
        click.echo()

        for item in result.payload:
            click.echo(item)

    except Exception as e:
        click.echo(f"Error listing authors: {e}", err=True)


@authors.command()
@click.argument("author_id")
@click.pass_context
def get(ctx: click.Context, author_id: str):
    """Get an author by ID."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        author = client.authors.get(author_id)
        click.echo(f"Author: {author.id}")
        click.echo(f"  Name: {author.name}")
        click.echo(f"  Handle: {author.handle}")
        if author.tagline:
            click.echo(f"  Tagline: {author.tagline}")
        if author.bio:
            click.echo(f"  Bio: {author.bio}")
        if author.email:
            click.echo(f"  Email: {author.email}")

        if author.social_links:
            click.echo("  Social Links:")
            if author.social_links.website:
                click.echo(f"    Website: {author.social_links.website}")
            if author.social_links.twitter:
                click.echo(f"    Twitter: {author.social_links.twitter}")
            if author.social_links.linkedin:
                click.echo(f"    LinkedIn: {author.social_links.linkedin}")
            if author.social_links.facebook:
                click.echo(f"    Facebook: {author.social_links.facebook}")

        if author.avatar:
            click.echo(f"  Avatar: {author.avatar}")
            if author.avatar_width and author.avatar_height:
                click.echo(
                    f"  Avatar Dimensions: {author.avatar_width}x{author.avatar_height}"
                )

        click.echo(f"  Created: {author.created_at}")
        click.echo(f"  Updated: {author.updated_at}")

    except Exception as e:
        click.echo(f"Error getting author: {e}", err=True)


@authors.command()
@click.argument("author_id")
@click.option("--name", help="New name for the author")
@click.option("--handle", help="New handle for the author")
@click.option("--tagline", help="New tagline for the author")
@click.option("--bio", help="New bio for the author")
@click.option("--email", help="New email for the author")
@click.option("--avatar", help="Path to new avatar image file")
@click.option("--social-links", help="New social links as JSON string")
@click.pass_context
def update(
    ctx: click.Context,
    author_id: str,
    name: Optional[str],
    handle: Optional[str],
    tagline: Optional[str],
    bio: Optional[str],
    email: Optional[str],
    avatar: Optional[str],
    social_links: Optional[str],
):
    """Update an author."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    # Parse social links JSON
    social_links_dict = None
    if social_links:
        try:
            social_links_dict = json.loads(social_links)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON format for social-links", err=True)
            return

    try:
        update_data = UpdateAuthor(
            name=name,
            handle=handle,
            tagline=tagline,
            bio=bio,
            email=email,
            avatar=avatar,
            social_links=social_links_dict,
        )
        author = client.authors.update(author_id, update_data)
        click.echo(f"Updated author: {author.id}")
        click.echo(f"  Name: {author.name}")
        click.echo(f"  Handle: {author.handle}")
        if author.tagline:
            click.echo(f"  Tagline: {author.tagline}")

    except Exception as e:
        click.echo(f"Error updating author: {e}", err=True)


@authors.command()
@click.argument("author_id")
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.pass_context
def delete(ctx: click.Context, author_id: str, confirm: bool):
    """Delete an author."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    if not confirm:
        if not click.confirm(f"Delete author {author_id}?"):
            return

    try:
        client.authors.delete(author_id)
        click.echo(f"Deleted author: {author_id}")

    except Exception as e:
        click.echo(f"Error deleting author: {e}", err=True)


if __name__ == "__main__":
    authors()
