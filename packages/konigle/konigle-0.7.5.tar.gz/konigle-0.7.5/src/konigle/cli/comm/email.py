"""
CLI commands for email communication operations.
"""

import os
from typing import Optional, cast

import click

from konigle import models
from konigle.cli.main import cli, get_client
from konigle.filters.comm import (
    EmailChannelFilters,
    EmailIdentityFilters,
    EmailTemplateFilters,
)
from konigle.models.comm.email.account import EmailAccountSetup
from konigle.models.comm.email.send import Email


def print_dns_records(records, record_type="DNS", domain_context=""):
    """Print DNS records in a consistent format."""
    if not records:
        return

    click.echo(f"\n🔧 {record_type} Records Required:")
    if domain_context:
        click.echo(f"Add the following records to your {domain_context} DNS:")
    else:
        click.echo("Add the following DNS records:")
    click.echo()

    for i, record in enumerate(records, 1):
        click.echo(f"Record {i}:")
        click.echo(f"  Type: {record.get('type', 'CNAME')}")
        click.echo(f"  Name: {record.get('name', '')}")
        if record.get("priority"):
            click.echo(f"  Priority: {record.get('priority')}")
        click.echo(f"  Value: {record.get('value', '')}")
        if record.get("description"):
            click.echo(f"  Purpose: {record.get('description')}")
        click.echo()


def print_verification_help(identity_id, record_type="verification"):
    """Print help text for DNS verification."""
    click.echo(
        "📝 Note: After adding these DNS records, it may take up to "
        "72 hours"
    )
    click.echo(f"   for {record_type} to complete. You can check status with:")
    click.echo(f"   konigle comm email identities check-status {identity_id}")


@cli.group()
def comm() -> None:
    """Communication management commands."""
    pass


@comm.group()
def email() -> None:
    """Email communication commands."""
    pass


# Email Accounts Commands
@email.group()
def accounts() -> None:
    """Email account management commands."""
    pass


@accounts.command("setup")
@click.option("--name", required=True, help="Name for the email account")
@click.option("--from-email", required=True, help="Default from email address")
@click.option("--reply-to-email", help="Default reply-to email address")
@click.option(
    "--identity-value", required=True, help="Domain or email for identity"
)
@click.pass_context
def setup_account(
    ctx: click.Context,
    name: str,
    from_email: str,
    reply_to_email: Optional[str],
    identity_value: str,
) -> None:
    """Setup a new email account with default channels and identity."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        setup_data = EmailAccountSetup(
            account_name=name,
            default_from_email=from_email,
            default_reply_to_email=reply_to_email,
            identity_value=identity_value,
        )

        result = client.email_accounts.setup(setup_data)

        account = result["account"]
        channels = result["channels"]
        identity = cast(models.EmailIdentity, result["identity"])

        click.echo("✓ Email account setup completed successfully!")
        click.echo("\n📧 Account Details:")
        click.echo(account)

        click.echo("\n📬 Default Channels Created:")
        for channel in channels:
            click.echo(channel)

        click.echo("\n🔐 Identity Created:")
        click.echo(f"  Type: {identity.identity_type}")
        click.echo(f"  Value: {identity.identity_value}")
        click.echo(f"  Verified: {identity.verified}")

        # Show DNS records for verification
        if identity.dkim_records:
            print_dns_records(
                identity.dkim_records,
                "DKIM",
                f"domain {identity.identity_value}",
            )
            print_verification_help(identity.id, "DKIM verification")

    except Exception as e:
        click.echo(f"✗ Error setting up email account: {e}", err=True)
        ctx.exit(1)


@accounts.command("create")
@click.option("--name", "-n", required=True, help="Account name")
@click.option("--from-email", help="Default from email address")
@click.option("--from-name", help="Default from name")
@click.option("--reply-to-email", help="Default reply-to email address")
@click.option("--reply-to-name", help="Default reply-to name")
@click.pass_context
def create_account(
    ctx: click.Context,
    name: str,
    from_email: Optional[str],
    from_name: Optional[str],
    reply_to_email: Optional[str],
    reply_to_name: Optional[str],
) -> None:
    """Create a new email account."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        account_data = models.EmailAccountCreate(
            name=name,
            default_from_email=from_email or "",
            default_from_name=from_name or "",
            default_reply_to_email=reply_to_email or "",
            default_reply_to_name=reply_to_name or "",
        )

        result = client.email_accounts.create(account_data)

        click.echo("✓ Email account created successfully!")
        click.echo(result)
        click.echo("Below are the next steps before you can send emails:")
        click.echo("1. Create one or more email channels.")
        click.echo("2. Add and verify email identities (domains or emails).")
        click.echo("3. Configure DNS records for domain identities.")
        click.echo("4. Start sending emails using the account, channels")

    except Exception as e:
        click.echo(f"✗ Error creating email account: {e}", err=True)
        ctx.exit(1)


@accounts.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.pass_context
def list_accounts(
    ctx: click.Context,
    page: int,
    page_size: int,
) -> None:
    """List email accounts."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        result = client.email_accounts.list(page=page, page_size=page_size)

        if not result.payload:
            click.echo("No email accounts found.")
            return

        click.echo(f"Email Accounts (page {page}):")
        click.echo()

        for account in result.payload:
            click.echo(account)

    except Exception as e:

        click.echo(f"✗ Error listing email accounts: {e}", err=True)
        ctx.exit(1)


@accounts.command("get")
@click.argument("account_id")
@click.pass_context
def get_account(ctx: click.Context, account_id: str) -> None:
    """Get an email account by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        account = client.email_accounts.get(account_id)

        click.echo("✓ Email account details:")
        click.echo(f"{account.model_dump_json(indent=2)}")

    except Exception as e:
        click.echo(f"✗ Error getting email account: {e}", err=True)
        ctx.exit(1)


@accounts.command("update")
@click.argument("account_id")
@click.option("--name", "-n", help="New account name")
@click.option("--from-email", help="New default from email address")
@click.option("--from-name", help="New default from name")
@click.option("--reply-to-email", help="New default reply-to email address")
@click.option("--reply-to-name", help="New default reply-to name")
@click.pass_context
def update_account(
    ctx: click.Context,
    account_id: str,
    name: Optional[str],
    from_email: Optional[str],
    from_name: Optional[str],
    reply_to_email: Optional[str],
    reply_to_name: Optional[str],
) -> None:
    """Update an email account."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if name:
            update_data["name"] = name
        if from_email is not None:
            update_data["default_from_email"] = from_email
        if from_name is not None:
            update_data["default_from_name"] = from_name
        if reply_to_email is not None:
            update_data["default_reply_to_email"] = reply_to_email
        if reply_to_name is not None:
            update_data["default_reply_to_name"] = reply_to_name

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        account_update = models.EmailAccountUpdate(**update_data)
        result = client.email_accounts.update(account_id, account_update)

        click.echo("✓ Email account updated successfully!")
        click.echo("Details:")
        click.echo(result.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error updating email account: {e}", err=True)
        ctx.exit(1)


@accounts.command("delete")
@click.argument("account_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_account(
    ctx: click.Context,
    account_id: str,
    yes: bool,
) -> None:
    """Delete an email account."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete email account {account_id}? All "
            "the associated channels, identities and other resources will "
            "also be deleted."
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.email_accounts.delete(account_id)

        click.echo(f"✓ Email account {account_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting email account: {e}", err=True)
        ctx.exit(1)


# Email Channels Commands
@email.group()
def channels() -> None:
    """Email channel management commands."""
    pass


@channels.command("create")
@click.option("--code", "-c", required=True, help="Channel code")
@click.option(
    "--type",
    "-t",
    "channel_type",
    required=True,
    type=click.Choice(["transactional", "marketing", "broadcast"]),
    help="Channel type",
)
@click.pass_context
def create_channel(
    ctx: click.Context,
    code: str,
    channel_type: str,
) -> None:
    """Create a new email channel."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        channel_data = models.EmailChannelCreate(
            code=code,
            channel_type=models.EmailChannelType(channel_type),
        )

        result = client.email_channels.create(channel_data)

        click.echo("✓ Email channel created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating email channel: {e}", err=True)
        ctx.exit(1)


@channels.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--search", "-q", help="Search in code and type")
@click.option("--type", "channel_type", help="Filter by channel type")
@click.option("--status", help="Filter by status")
@click.pass_context
def list_channels(
    ctx: click.Context,
    page: int,
    page_size: int,
    search: Optional[str],
    channel_type: Optional[str],
    status: Optional[str],
) -> None:
    """List email channels."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = EmailChannelFilters(
            q=search,
            channel_type=channel_type,
            status=status,
        )

        result = client.email_channels.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No email channels found.")
            return

        click.echo(f"Email Channels (page {page}):")
        click.echo()

        for channel in result.payload:
            click.echo(channel)

    except Exception as e:

        click.echo(f"✗ Error listing email channels: {e}", err=True)
        ctx.exit(1)


@channels.command("get")
@click.argument("channel_id")
@click.pass_context
def get_channel(ctx: click.Context, channel_id: str) -> None:
    """Get an email channel by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        channel = client.email_channels.get(channel_id)

        click.echo("✓ Email channel details:")
        click.echo(f"{channel.model_dump_json(indent=2)}")

    except Exception as e:
        click.echo(f"✗ Error getting email channel: {e}", err=True)
        ctx.exit(1)


@channels.command("update")
@click.argument("channel_id")
@click.option("--code", "-c", help="New channel code")
@click.pass_context
def update_channel(
    ctx: click.Context,
    channel_id: str,
    code: Optional[str],
) -> None:
    """Update an email channel."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if code:
            update_data["code"] = code

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        channel_update = models.EmailChannelUpdate(**update_data)
        result = client.email_channels.update(channel_id, channel_update)

        click.echo("✓ Email channel updated successfully!")
        click.echo("Details:")
        click.echo(result.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error updating email channel: {e}", err=True)
        ctx.exit(1)


@channels.command("delete")
@click.argument("channel_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_channel(
    ctx: click.Context,
    channel_id: str,
    yes: bool,
) -> None:
    """Delete an email channel."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete email channel {channel_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.email_channels.delete(channel_id)

        click.echo(f"✓ Email channel {channel_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting email channel: {e}", err=True)
        ctx.exit(1)


# Email Identities Commands
@email.group()
def identities() -> None:
    """Email identity management commands."""
    pass


@identities.command("create")
@click.option("--value", "-v", required=True, help="Domain or email address")
@click.pass_context
def create_identity(
    ctx: click.Context,
    value: str,
) -> None:
    """Create a new email identity."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        identity_data = models.EmailIdentityCreate(
            identity_value=value,
        )

        result = client.email_identities.create(identity_data)

        click.echo("✓ Email identity created successfully!")
        click.echo(result)
        click.echo(
            f"Status: {'Verified' if result.verified else 'Pending Verification'}"
        )

        # Show DKIM records if available
        if result.dkim_records:
            print_dns_records(
                result.dkim_records, "DKIM", f"domain {result.identity_value}"
            )
            print_verification_help(result.id, "DKIM verification")

    except Exception as e:
        click.echo(f"✗ Error creating email identity: {e}", err=True)
        ctx.exit(1)


@identities.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--search", "-q", help="Search in identity value")
@click.option(
    "--type", "identity_type", help="Filter by identity type (domain/email)"
)
@click.pass_context
def list_identities(
    ctx: click.Context,
    page: int,
    page_size: int,
    search: Optional[str],
    identity_type: Optional[str],
) -> None:
    """List email identities."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filter_data = {}
        if search:
            filter_data["q"] = search
        if identity_type in ["domain", "email"]:
            filter_data["identity_type"] = identity_type

        filters = EmailIdentityFilters(**filter_data)

        result = client.email_identities.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No email identities found.")
            return

        click.echo(f"Email Identities (page {page}):")
        click.echo()

        for identity in result.payload:
            click.echo(identity)

    except Exception as e:
        click.echo(f"✗ Error listing email identities: {e}", err=True)
        ctx.exit(1)


@identities.command("get")
@click.argument("identity_id")
@click.pass_context
def get_identity(ctx: click.Context, identity_id: str) -> None:
    """Get an email identity by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        identity = client.email_identities.get(identity_id)

        click.echo("✓ Email identity details:")
        click.echo(f"{identity.model_dump_json(indent=2)}")

    except Exception as e:
        click.echo(f"✗ Error getting email identity: {e}", err=True)
        ctx.exit(1)


@identities.command("update")
@click.argument("identity_id")
@click.option(
    "--use-custom-mail-from/--no-custom-mail-from",
    help="Toggle custom MAIL FROM usage",
)
@click.pass_context
def update_identity(
    ctx: click.Context,
    identity_id: str,
    use_custom_mail_from: Optional[bool],
) -> None:
    """Update an email identity."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if use_custom_mail_from is not None:
            update_data["use_custom_mail_from"] = use_custom_mail_from

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        identity_update = models.EmailIdentityUpdate(**update_data)
        result = client.email_identities.update(identity_id, identity_update)

        click.echo("✓ Email identity updated successfully!")
        click.echo("Details:")
        click.echo(result.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error updating email identity: {e}", err=True)
        ctx.exit(1)


@identities.command("delete")
@click.argument("identity_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_identity(
    ctx: click.Context,
    identity_id: str,
    yes: bool,
) -> None:
    """Delete an email identity."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete email identity {identity_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.email_identities.delete(identity_id)

        click.echo(f"✓ Email identity {identity_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting email identity: {e}", err=True)
        ctx.exit(1)


@identities.command("check-status")
@click.argument("identity_id")
@click.pass_context
def check_verification_status(ctx: click.Context, identity_id: str) -> None:
    """Check verification status for an email identity."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        identity = client.email_identities.check_verification_status(
            identity_id
        )

        click.echo("✓ Verification status checked:")
        click.echo(f"{identity.model_dump_json(indent=2)}")

    except Exception as e:
        click.echo(f"✗ Error checking verification status: {e}", err=True)
        ctx.exit(1)


@identities.command("setup-mail-from")
@click.argument("identity_id")
@click.argument("mail_from_domain")
@click.pass_context
def setup_custom_mail_from(
    ctx: click.Context, identity_id: str, mail_from_domain: str
) -> None:
    """Setup custom MAIL FROM domain for an email identity."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        identity = client.email_identities.setup_custom_mail_from(
            identity_id, mail_from_domain
        )

        click.echo("✓ Custom MAIL FROM domain setup successfully:")
        click.echo(f"Identity: {identity.identity_value}")
        click.echo(f"MAIL FROM Domain: {identity.mail_from_domain}")
        click.echo(f"Status: {identity.mail_from_verification_status}")

        # Show MAIL FROM records if available
        if identity.mail_from_records and identity.mail_from_domain:
            print_dns_records(
                identity.mail_from_records,
                "MAIL FROM",
                identity.mail_from_domain,
            )
            print_verification_help(identity.id, "MAIL FROM verification")
    except Exception as e:
        click.echo(f"✗ Error setting up custom MAIL FROM: {e}", err=True)
        ctx.exit(1)


# Email Send Commands
@email.command("send")
@click.option(
    "--to",
    "to_emails",
    multiple=True,
    required=True,
    help="Recipient email addresses (can be used multiple times)",
)
@click.option("--subject", "-s", required=True, help="Email subject")
@click.option("--body-html", required=True, help="HTML body content")
@click.option("--body-text", help="Plain text body content (optional)")
@click.option(
    "--from-email", help="From email address (overrides account default)"
)
@click.option("--reply-to-email", help="Reply-to email address")
@click.option("--channel", "-c", required=True, help="Channel code to use")
@click.option("--category", help="Notification category code")
@click.option(
    "--attachment",
    "attachments",
    multiple=True,
    help="File attachments (can be used multiple times, max 10)",
)
@click.option(
    "--save-as-template",
    is_flag=True,
    help="Save email as template for future use",
)
@click.pass_context
def send_email(
    ctx: click.Context,
    to_emails: tuple,
    subject: str,
    body_html: str,
    body_text: Optional[str],
    from_email: Optional[str],
    reply_to_email: Optional[str],
    channel: str,
    category: Optional[str],
    attachments: tuple,
    save_as_template: bool,
) -> None:
    """Send an email through the Konigle email service."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        # Validate attachment count
        if len(attachments) > 10:
            click.echo("✗ Error: Maximum 10 attachments allowed", err=True)
            ctx.exit(1)

        # Process attachments - validate file paths exist
        processed_attachments = []
        for path in attachments:
            try:
                if not os.path.exists(path):
                    click.echo(
                        f"✗ Error: Attachment file not found: {path}",
                        err=True,
                    )
                    ctx.exit(1)
                if not os.path.isfile(path):
                    click.echo(
                        f"✗ Error: Attachment path is not a file: {path}",
                        err=True,
                    )
                    ctx.exit(1)
                # For CLI, we expect file paths as strings
                processed_attachments.append(path)
            except Exception as e:
                click.echo(
                    f"✗ Error processing attachment {path}: {e}",
                    err=True,
                )
                ctx.exit(1)

        email_data = Email(
            to_email=list(to_emails),
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            from_email=from_email,
            reply_to_email=reply_to_email,
            channel=channel,
            category=category,
            attachments=(
                processed_attachments if processed_attachments else None
            ),
            save_as_template=save_as_template,
        )

        result = client.emails.send(email_data)

        click.echo("✓ Email sent successfully!")
        click.echo(f"Status: {result.status}")
        if result.message_id:
            click.echo(f"Message ID: {result.message_id}")
        if result.template_id:
            click.echo(f"Template ID: {result.template_id}")

    except Exception as e:
        import traceback

        traceback.print_exc()
        click.echo(f"✗ Error sending email: {e}", err=True)
        ctx.exit(1)


# Email Templates Commands
@email.group()
def templates() -> None:
    """Email template management commands."""
    pass


@templates.command("create")
@click.option("--name", "-n", required=True, help="Template name")
@click.option("--code", "-c", required=True, help="Template code")
@click.option("--subject", "-s", required=True, help="Subject template")
@click.option("--body-html", required=True, help="HTML body template")
@click.option("--body-text", help="Plain text body template (optional)")
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Tags for categorizing template (can be used multiple times)",
)
@click.pass_context
def create_template(
    ctx: click.Context,
    name: str,
    code: str,
    subject: str,
    body_html: str,
    body_text: Optional[str],
    tags: tuple,
) -> None:
    """Create a new email template."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        template_data = models.EmailTemplateCreate(
            name=name,
            code=code,
            subject=subject,
            body_html=body_html,
            body_text=body_text or "",
            tags=list(tags) if tags else [],
        )

        result = client.email_templates.create(template_data)

        click.echo("✓ Email template created successfully!")
        click.echo(result)

    except Exception as e:
        click.echo(f"✗ Error creating email template: {e}", err=True)
        ctx.exit(1)


@templates.command("list")
@click.option("--page", "-p", default=1, help="Page number (default: 1)")
@click.option(
    "--page-size", "-s", default=10, help="Items per page (default: 10)"
)
@click.option("--search", "-q", help="Search in name, code, and tags")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option(
    "--ordering",
    help="Order by field (name, code, created_at, updated_at). "
    "Prefix with '-' for descending",
)
@click.pass_context
def list_templates(
    ctx: click.Context,
    page: int,
    page_size: int,
    search: Optional[str],
    tags: Optional[str],
    ordering: Optional[str],
) -> None:
    """List email templates."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        filters = EmailTemplateFilters(
            q=search,
            tags=tags,
            ordering=ordering,  # type: ignore
        )

        result = client.email_templates.list(
            page=page, page_size=page_size, filters=filters
        )

        if not result.payload:
            click.echo("No email templates found.")
            return

        click.echo(f"Email Templates (page {page}):")
        click.echo()

        for template in result.payload:
            click.echo(template)

    except Exception as e:
        click.echo(f"✗ Error listing email templates: {e}", err=True)
        ctx.exit(1)


@templates.command("get")
@click.argument("template_id")
@click.pass_context
def get_template(ctx: click.Context, template_id: str) -> None:
    """Get an email template by ID."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        template = client.email_templates.get(template_id)

        click.echo("✓ Email template details:")
        click.echo(f"{template.model_dump_json(indent=2)}")

    except Exception as e:
        click.echo(f"✗ Error getting email template: {e}", err=True)
        ctx.exit(1)


@templates.command("update")
@click.argument("template_id")
@click.option("--name", "-n", help="New template name")
@click.option("--code", "-c", help="New template code")
@click.option("--subject", "-s", help="New subject template")
@click.option("--body-html", help="New HTML body template")
@click.option("--body-text", help="New plain text body template")
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Replace tags with new ones (can be used multiple times)",
)
@click.pass_context
def update_template(
    ctx: click.Context,
    template_id: str,
    name: Optional[str],
    code: Optional[str],
    subject: Optional[str],
    body_html: Optional[str],
    body_text: Optional[str],
    tags: tuple,
) -> None:
    """Update an email template."""
    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if code is not None:
            update_data["code"] = code
        if subject is not None:
            update_data["subject"] = subject
        if body_html is not None:
            update_data["body_html"] = body_html
        if body_text is not None:
            update_data["body_text"] = body_text
        if tags:
            update_data["tags"] = list(tags)

        if not update_data:
            click.echo("No update fields provided.", err=True)
            ctx.exit(1)

        template_update = models.EmailTemplateUpdate(**update_data)
        result = client.email_templates.update(template_id, template_update)

        click.echo("✓ Email template updated successfully!")
        click.echo("Details:")
        click.echo(result.model_dump_json(indent=2))

    except Exception as e:
        click.echo(f"✗ Error updating email template: {e}", err=True)
        ctx.exit(1)


@templates.command("delete")
@click.argument("template_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_template(
    ctx: click.Context,
    template_id: str,
    yes: bool,
) -> None:
    """Delete an email template."""
    if not yes:
        if not click.confirm(
            f"Are you sure you want to delete email template "
            f"{template_id}?"
        ):
            click.echo("Cancelled.")
            return

    try:
        client = get_client(ctx.obj["api_key"], ctx.obj["base_url"])
        client.email_templates.delete(template_id)

        click.echo(f"✓ Email template {template_id} deleted successfully!")

    except Exception as e:
        click.echo(f"✗ Error deleting email template: {e}", err=True)
        ctx.exit(1)
