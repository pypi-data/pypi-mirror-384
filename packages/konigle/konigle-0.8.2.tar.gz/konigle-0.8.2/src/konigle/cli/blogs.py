"""
CLI commands for blog operations.
"""

import json
from typing import Optional

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.website import BlogFilters


@cli.group()
def blogs() -> None:
    """Blog management commands."""
    pass


@blogs.command()
@click.option("--title", "-t", required=True, help="Blog post title")
@click.option(
    "--name", "-n", help="Blog post name (defaults to title if not provided)"
)
@click.option(
    "--handle", "-h", help="URL handle (auto-generated if not provided)"
)
@click.option(
    "--content", "-c", help="Blog post content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.option("--summary", "-s", help="Blog post summary")
@click.option("--folder", "-f", help="Folder ID to place the blog post in")
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
    folder: Optional[str],
    author: Optional[str],
) -> None:
    """Create a new blog post."""
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

        blog_data = models.BlogCreate(
            title=title,
            name=name,
            handle=handle,
            content=content_data,
            summary=summary or "",
            folder=folder,
            author=author,
        )

        result = client.blogs.create(blog_data)

        click.echo("✓ Blog post created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating blog post: {e}", err=True)
        ctx.exit(1)


@blogs.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--folder", "-f", help="Filter by folder ID")
@click.option("--published", is_flag=True, help="Filter by published status")
@click.option(
    "--unpublished", is_flag=True, help="Filter by unpublished status"
)
@click.option("--handle", "-H", help="Filter by blog post handle")
@click.pass_context
def list_blogs(
    ctx: click.Context,
    page: int,
    page_size: int,
    folder: Optional[str],
    published: Optional[bool],
    unpublished: Optional[bool],
    handle: Optional[str],
) -> None:
    """List blog posts."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        if published and unpublished:
            click.echo(
                "Error: Cannot use both --published and --unpublished filters together.",
                err=True,
            )
            ctx.exit(1)

        filters = BlogFilters(
            folder=folder,
            published=(
                published if published else (False if unpublished else None)
            ),
            handle=handle,
        )

        result = client.blogs.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No blog posts found.")
            return

        click.echo(f"Blog posts (page {page}):")
        click.echo()

        for blog in result.payload:
            click.echo(blog)

    except Exception as e:
        click.echo(f"✗ Error listing blog posts: {e}", err=True)
        ctx.exit(1)


@blogs.command()
@click.argument("blog_id")
@click.pass_context
def get(ctx: click.Context, blog_id: str) -> None:
    """Get a blog post by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        blog = client.blogs.get(blog_id)

        click.echo("✓ Fetched blog post successfully!")
        click.echo(blog)

        click.echo("Details:")
        click.echo(blog.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error getting blog post: {e}", err=True)
        ctx.exit(1)


@blogs.command()
@click.argument("blog_id")
@click.option("--title", "-t", help="New blog post title")
@click.option("--name", "-n", help="New blog post name")
@click.option(
    "--content", "-c", help="New blog post content as EditorJS JSON string"
)
@click.option(
    "--content-file",
    type=click.Path(exists=True, readable=True),
    help="Path to EditorJS JSON content file",
)
@click.option("--summary", "-s", help="New blog post summary")
@click.option("--json-ld", "-j", help="JSON-LD structured data as JSON string")
@click.option("--seo", "-m", help="SEO meta as JSON string")
@click.pass_context
def update(
    ctx: click.Context,
    blog_id: str,
    title: Optional[str],
    name: Optional[str],
    content: Optional[str],
    content_file: Optional[str],
    summary: Optional[str],
    json_ld: Optional[str],
    seo: Optional[str],
) -> None:
    """Update a blog post."""
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

        blog_update = models.BlogUpdate(**update_data)
        result = client.blogs.update(blog_id, blog_update)

        click.echo("✓ Blog post updated successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error updating blog post: {e}", err=True)
        ctx.exit(1)


@blogs.command()
@click.argument("blog_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(
    ctx: click.Context,
    blog_id: str,
    yes: bool,
) -> None:
    """Delete a blog post."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete blog post {blog_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.blogs.delete(blog_id)

        click.echo(f"✓ Blog post {blog_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting blog post: {e}", err=True)
        ctx.exit(1)


@blogs.command()
@click.argument("blog_id")
@click.pass_context
def publish(ctx: click.Context, blog_id: str) -> None:
    """Publish a blog post."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.blogs.publish(blog_id)

        click.echo(f"✓ Blog post {blog_id} published successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error publishing blog post: {e}", err=True)
        ctx.exit(1)


@blogs.command()
@click.argument("blog_id")
@click.pass_context
def unpublish(ctx: click.Context, blog_id: str) -> None:
    """Unpublish a blog post."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.blogs.unpublish(blog_id)

        click.echo(f"✓ Blog post {blog_id} unpublished successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error unpublishing blog post: {e}", err=True)
        ctx.exit(1)


@blogs.command("change-handle")
@click.argument("blog_id")
@click.argument("new_handle")
@click.option(
    "--redirect", "-r", is_flag=True, help="Create redirect from old handle"
)
@click.pass_context
def change_handle(
    ctx: click.Context, blog_id: str, new_handle: str, redirect: bool
) -> None:
    """Change the handle of a blog post."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        result = client.blogs.change_handle(blog_id, new_handle, redirect)

        click.echo(f"✓ Blog post {blog_id} handle changed to '{new_handle}'!")
        if redirect:
            click.echo("✓ Redirect created from old handle.")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error changing blog post handle: {e}", err=True)
        ctx.exit(1)
