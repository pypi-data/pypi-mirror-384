"""CLI commands for website and business information management."""

import click

from konigle.cli.main import cli, get_client


@cli.group()
def website():
    """Manage website and business information."""
    pass


@website.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save business info to file",
)
@click.pass_context
def get_business_info(ctx: click.Context, output: str | None):
    """Get the business information."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        content = client.website.get_business_info()

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"✅ Business info saved to {output}")
        else:
            click.echo(content)

    except Exception as e:
        click.echo(f"Error getting business info: {e}", err=True)


@website.command()
@click.option(
    "--content",
    help="Business information as string",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, readable=True),
    help="Path to business info file",
)
@click.pass_context
def set_business_info(
    ctx: click.Context,
    content: str | None,
    file: str | None,
):
    """Set the business information."""
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
    info_content = content
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                info_content = f.read()
        except Exception as e:
            click.echo(f"Error reading file: {e}", err=True)
            return

    try:
        client.website.set_business_info(info_content or "")
        click.echo("✅ Business info updated successfully")

    except Exception as e:
        click.echo(f"Error setting business info: {e}", err=True)


@website.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save website info to file",
)
@click.pass_context
def get_website_info(ctx: click.Context, output: str | None):
    """Get the website information."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        content = client.website.get_website_info()

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"✅ Website info saved to {output}")
        else:
            click.echo(content)

    except Exception as e:
        click.echo(f"Error getting website info: {e}", err=True)


@website.command()
@click.option(
    "--content",
    help="Website information as string",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, readable=True),
    help="Path to website info file",
)
@click.pass_context
def set_website_info(
    ctx: click.Context,
    content: str | None,
    file: str | None,
):
    """Set the website information."""
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
    info_content = content
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                info_content = f.read()
        except Exception as e:
            click.echo(f"Error reading file: {e}", err=True)
            return

    try:
        client.website.set_website_info(info_content or "")
        click.echo("✅ Website info updated successfully")

    except Exception as e:
        click.echo(f"Error setting website info: {e}", err=True)


@website.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save design system to file",
)
@click.pass_context
def get_design_system(ctx: click.Context, output: str | None):
    """Get the design system information."""
    client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

    try:
        content = client.website.get_design_system()

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"✅ Design system saved to {output}")
        else:
            click.echo(content)

    except Exception as e:
        click.echo(f"Error getting design system: {e}", err=True)


@website.command()
@click.option(
    "--content",
    help="Design system information as string",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, readable=True),
    help="Path to design system file",
)
@click.pass_context
def set_design_system(
    ctx: click.Context,
    content: str | None,
    file: str | None,
):
    """Set the design system information."""
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
    info_content = content
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                info_content = f.read()
        except Exception as e:
            click.echo(f"Error reading file: {e}", err=True)
            return

    try:
        client.website.set_design_system(info_content or "")
        click.echo("✅ Design system updated successfully")

    except Exception as e:
        click.echo(f"Error setting design system: {e}", err=True)


if __name__ == "__main__":
    website()
