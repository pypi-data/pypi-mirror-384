"""CLI commands for design system stylesheet management."""

import click

from konigle.cli.main import cli, get_client


@cli.group()
def design():
    """Manage design system stylesheets."""
    pass


@design.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save stylesheet content to file",
)
@click.pass_context
def get_stylesheet(ctx: click.Context, output: str | None):
    """Get the design system stylesheet content."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        content = client.stylesheets.get_content()

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"✅ Stylesheet saved to {output}")
        else:
            click.echo(content)

    except Exception as e:
        click.echo(f"Error getting stylesheet: {e}", err=True)


@design.command()
@click.option(
    "--content",
    help="Stylesheet content as string",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, readable=True),
    help="Path to stylesheet file",
)
@click.pass_context
def set_stylesheet(
    ctx: click.Context,
    content: str | None,
    file: str | None,
):
    """Set the design system stylesheet content."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    # Validate input
    if not content and not file:
        click.echo(
            "Error: Either --content or --file must be provided", err=True
        )
        return

    if content and file:
        click.echo("Error: Cannot specify both --content and --file", err=True)
        return

    # Get content from file or direct input
    stylesheet_content = content
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                stylesheet_content = f.read()
        except Exception as e:
            click.echo(f"Error reading file: {e}", err=True)
            return

    try:
        client.stylesheets.set_content(stylesheet_content or "")
        click.echo("✅ Stylesheet content updated successfully")

    except Exception as e:
        click.echo(f"Error setting stylesheet: {e}", err=True)


if __name__ == "__main__":
    design()
