"""
Init command for the Euno SDK.

This command handles initial setup and token validation.
"""

import click
from .config import config
from .api import api_client


def init_command() -> None:
    """Initialize the Euno SDK with a user token."""
    click.echo("🚀 Welcome to the Euno SDK!")
    click.echo()

    # Check if already configured
    if config.is_configured():
        if not click.confirm("Euno SDK is already configured. Do you want to reconfigure?"):
            click.echo("Configuration unchanged.")
            return

    click.echo("To get started, you'll need an API token from your Euno account.")
    click.echo("You can find this in your Euno dashboard under Settings > API Keys.")
    click.echo()

    # Get token
    token = click.prompt("Enter your Euno API token", hide_input=True)

    if not token.strip():
        click.echo("❌ Token cannot be empty.")
        return

    # Get account ID
    account_id = click.prompt("Enter your account ID")

    if not account_id.strip():
        click.echo("❌ Account ID cannot be empty.")
        return

    # Validate token
    click.echo("🔍 Validating token...")
    try:
        user_info = api_client.validate_token(token)

        click.echo("✅ Token validated successfully!")
        click.echo(f"👤 Logged in as: {user_info.get('email', 'Unknown')}")

        # Store configuration
        config.set_token(token)
        config.set_backend_url(config.get_backend_url())
        config.set_account_id(account_id)

        click.echo()
        click.echo("🎉 Euno SDK initialized successfully!")
        click.echo("You can now use other Euno commands.")

    except Exception as e:
        click.echo(f"❌ Token validation failed: {str(e)}")
        click.echo("Please check your token and try again.")


def status_command() -> None:
    """Show the current configuration status."""
    if not config.is_configured():
        click.echo("❌ Euno SDK is not configured.")
        click.echo("Run 'euno init' to get started.")
        return

    token = config.get_token()
    backend_url = config.get_backend_url()
    account_id = config.get_account_id()

    click.echo("✅ Euno SDK is configured")
    click.echo(f"Backend URL: {backend_url}")
    token_display = "*" * (len(token) - 4) + token[-4:] if token and len(token) > 4 else "****"
    click.echo(f"Token: {token_display}")
    click.echo(f"Account ID: {account_id}")

    # Validate current token
    try:
        if not token:
            click.echo("⚠️  No token configured")
            return

        user_info = api_client.validate_token(token)
        click.echo(f"👤 User: {user_info.get('email', 'Unknown')}")
        click.echo("✅ Token is valid")

        # Check account permissions if account ID is available
        if account_id:
            try:
                permissions = api_client.get_account_permissions(token, account_id)
                if permissions and len(permissions) > 0:
                    click.echo("✅ Account permissions: OK")
                else:
                    click.echo("❌ Account permissions: User has no role in the account")
            except Exception:
                click.echo("❌ Account permissions: User has no role in the account")
        else:
            click.echo("⚠️  No account ID configured")

    except Exception as e:
        click.echo(f"⚠️  Token validation failed: {str(e)}")
        click.echo("Run 'euno init' to reconfigure.")


def logout_command() -> None:
    """Clear the stored configuration."""
    if not config.is_configured():
        click.echo("❌ Euno SDK is not configured.")
        return

    if click.confirm("Are you sure you want to log out?"):
        config.clear_token()
        click.echo("✅ Logged out successfully.")
    else:
        click.echo("Logout cancelled.")
