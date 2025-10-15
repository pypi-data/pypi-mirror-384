"""
Command-line interface for the Euno SDK.

This module provides the CLI functionality accessible via the 'euno' command.
"""

import click
import json
import csv
import io
from typing import List, Optional, Dict, Any
from .core import hello_world, get_version
from .auth import init_command, status_command, logout_command
from .resources import list_resources
from .metadata_tags import list_metadata_tags, set_metadata_tag_value


def _display_csv(response: Dict[str, Any], requested_properties: Optional[List[str]] = None) -> None:
    """Display search results in CSV format."""
    resources = response.get("resources", [])
    if not resources:
        click.echo("No resources found.")
        return

    # Determine property order
    if requested_properties:
        # Use the order specified in the request
        properties = requested_properties
    else:
        # Get all unique property names from the resources and sort alphabetically
        all_properties = set()
        for resource in resources:
            all_properties.update(resource.keys())
        properties = sorted(list(all_properties))

    # Create CSV output
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(properties)

    # Write data rows
    for resource in resources:
        row = [resource.get(prop, "") for prop in properties]
        writer.writerow(row)

    click.echo(output.getvalue())


def _display_pretty(response: Dict[str, Any]) -> None:
    """Display search results in a pretty table format."""
    resources = response.get("resources", [])
    count = response.get("count", 0)

    if not resources:
        click.echo("No resources found.")
        return

    click.echo(f"Found {count} resources (showing {len(resources)}):")
    click.echo()

    # Get all unique property names
    all_properties = set()
    for resource in resources:
        all_properties.update(resource.keys())

    # Convert to sorted list, prioritizing common properties
    priority_props = ["uri", "type", "name"]
    properties = []

    # Add priority properties first if they exist
    for prop in priority_props:
        if prop in all_properties:
            properties.append(prop)
            all_properties.remove(prop)

    # Add remaining properties
    properties.extend(sorted(all_properties))

    # Calculate column widths
    col_widths = {}
    for prop in properties:
        col_widths[prop] = max(len(prop), max(len(str(resource.get(prop, ""))) for resource in resources))
        col_widths[prop] = min(col_widths[prop], 50)  # Cap at 50 characters

    # Print header
    header = " | ".join(prop.ljust(col_widths[prop]) for prop in properties)
    click.echo(header)
    click.echo("-" * len(header))

    # Print data rows
    for resource in resources:
        row = []
        for prop in properties:
            value = str(resource.get(prop, ""))
            if len(value) > 50:
                value = value[:47] + "..."
            row.append(value.ljust(col_widths[prop]))
        click.echo(" | ".join(row))


@click.group()
@click.version_option(version=get_version(), prog_name="euno-sdk")
def main() -> None:
    """
    Euno SDK - A Python library and CLI tool for interacting with Euno instances.

    This tool provides both programmatic access to Euno functionality
    and a command-line interface for common operations.
    """
    pass


@main.command()
@click.option("--name", "-n", default="World", help="Name to greet")
def hello_world_cmd(name: str) -> None:
    """
    A simple hello world command to demonstrate the CLI.

    Example:
        euno hello-world --name Euno
    """
    message = hello_world(name)
    click.echo(message)


@main.command()
def version() -> None:
    """Show the version of the Euno SDK."""
    click.echo(f"Euno SDK version: {get_version()}")


@main.command()
def init() -> None:
    """
    Initialize the Euno SDK with your API token.

    This command will prompt you for your Euno API token and validate it
    against the Euno backend. The token will be stored securely for future use.

    Example:
        euno init
    """
    init_command()


@main.command()
def status() -> None:
    """
    Show the current configuration status.

    Displays information about the current configuration including
    backend URL, token status, and user information.

    Example:
        euno status
    """
    status_command()


@main.command()
def logout() -> None:
    """
    Clear the stored configuration and log out.

    This will remove the stored API token and require you to run
    'euno init' again to authenticate.

    Example:
        euno logout
    """
    logout_command()


@main.group()
def resources() -> None:
    """Commands for working with Euno data model resources."""
    pass


@resources.command("list")
@click.option("--eql", "-e", help="Euno Query Language expression")
@click.option(
    "--properties",
    "-p",
    default="uri,type,name",
    help="Comma-separated list of properties (default: uri,type,name)",
)
@click.option("--page", default=1, help="Page number (default: 1)")
@click.option("--page-size", default=50, help="Number of resources per page (default: 50)")
@click.option("--sorting", "-s", help="Sorting specification")
@click.option("--relationships", "-r", help="Comma-separated list of relationships")
@click.option(
    "--format",
    "-f",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "pretty"]),
    help="Output format (default: json)",
)
def list_resources_cmd(
    eql: str,
    properties: str,
    page: int,
    page_size: int,
    sorting: str,
    relationships: str,
    output_format: str,
) -> None:
    """
    List resources from the Euno data model.

    Examples:
        euno resources list
        euno resources list --eql "has child(true, 1)" --properties "uri,name,type" \
            --format pretty
        euno resources list --relationships "parent,child" --page-size 20
    """
    try:
        # Use the library function
        response = list_resources(
            eql=eql,
            properties=properties,
            page=page,
            page_size=page_size,
            sorting=sorting,
            relationships=relationships,
        )

        # Format and display results
        if output_format == "json":
            click.echo(json.dumps(response, indent=2))
        elif output_format == "csv":
            requested_props = properties.split(",") if properties else None
            _display_csv(response, requested_props)
        elif output_format == "pretty":
            _display_pretty(response)
        else:
            click.echo(f"❌ Unknown format: {output_format}. Supported formats: json, csv, pretty")

    except Exception as e:
        click.echo(f"❌ Error searching resources: {str(e)}")


@main.group()
def metadata_tags() -> None:
    """Commands for working with metadata tags (custom properties)."""
    pass


@metadata_tags.command("list")
@click.option(
    "--format",
    "-f",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "pretty"]),
    help="Output format (default: json)",
)
def list_metadata_tags_cmd(output_format: str) -> None:
    """
    List all metadata tags (custom properties) for the configured account.

    Examples:
        euno metadata-tags list
        euno metadata-tags list --format pretty
        euno metadata-tags list --format csv
    """
    try:
        metadata_tags = list_metadata_tags()

        if output_format == "json":
            click.echo(json.dumps(metadata_tags, indent=2))
        elif output_format == "csv":
            if not metadata_tags:
                click.echo("No metadata tags found.")
                return

            # Get all unique property names and sort alphabetically
            all_properties: set = set()
            for tag in metadata_tags:
                all_properties.update(tag.keys())
            properties = sorted(list(all_properties))

            # Create CSV output
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(properties)

            # Write data rows
            for tag in metadata_tags:
                row = [tag.get(prop, "") for prop in properties]
                writer.writerow(row)

            click.echo(output.getvalue())
        elif output_format == "pretty":
            if not metadata_tags:
                click.echo("No metadata tags found.")
                return

            click.echo(f"Found {len(metadata_tags)} metadata tags:")
            click.echo()

            for i, tag in enumerate(metadata_tags, 1):
                click.echo(f"{i}. {tag.get('name', 'Unnamed')} (ID: {tag.get('id', 'N/A')})")
                if tag.get("description"):
                    click.echo(f"   Description: {tag['description']}")
                if tag.get("type"):
                    click.echo(f"   Type: {tag['type']}")
                click.echo()

    except Exception as e:
        click.echo(f"❌ Error listing metadata tags: {str(e)}")


@metadata_tags.command("set-value")
@click.argument("cp_id", type=int)
@click.argument("value_updates", type=str)
@click.option(
    "--format",
    "-f",
    "output_format",
    default="json",
    type=click.Choice(["json", "pretty"]),
    help="Output format (default: json)",
)
def set_metadata_tag_value_cmd(cp_id: int, value_updates: str, output_format: str) -> None:
    """
    Set values for a metadata tag (custom property).

    CP_ID: The custom property ID
    VALUE_UPDATES: JSON string containing the value updates

    Examples:
        euno metadata-tags set-value 123 '[{"resource_uri": "table://schema.table", "value": "production"}]'
        euno metadata-tags set-value 456 '[{"resource_uri": "table://schema.table", "value": "production"}]' \
            --format pretty
    """
    try:
        # Parse the JSON string
        try:
            value_updates_list = json.loads(value_updates)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Invalid JSON in value_updates: {str(e)}")
            return

        if not isinstance(value_updates_list, list):
            click.echo("❌ value_updates must be a JSON array")
            return

        result = set_metadata_tag_value(cp_id, value_updates_list)

        if output_format == "json":
            click.echo(json.dumps(result, indent=2))
        elif output_format == "pretty":
            click.echo("✅ Successfully set metadata tag values")
            click.echo(f"Custom Property ID: {cp_id}")
            click.echo(f"Updates applied: {len(value_updates_list)}")

    except Exception as e:
        click.echo(f"❌ Error setting metadata tag value: {str(e)}")


if __name__ == "__main__":
    main()
