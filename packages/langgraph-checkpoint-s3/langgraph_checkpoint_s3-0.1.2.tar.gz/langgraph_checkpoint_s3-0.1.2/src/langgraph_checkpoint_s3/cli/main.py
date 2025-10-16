"""Main CLI entry point for S3 checkpoint reader."""

import asyncio
import json
import sys
from typing import Any

import aioboto3
import click

from .reader import S3CheckpointReader, parse_s3_uri


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles special types."""

    def default(self, obj: Any) -> Any:
        """Handle special object types for JSON serialization."""
        # Handle bytes objects
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        # Handle other non-serializable objects by converting to string
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def output_json(data: dict[str, Any]) -> None:
    """Output data as JSON to stdout."""
    try:
        json.dump(data, sys.stdout, cls=JSONEncoder, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    except Exception as e:
        click.echo(f"Error serializing output to JSON: {e}", err=True)
        sys.exit(5)


def handle_error(error: Exception, exit_code: int) -> None:
    """Handle errors by printing to stderr and exiting with appropriate code."""
    click.echo(f"Error: {error}", err=True)
    sys.exit(exit_code)


def create_aioboto3_session(profile: str | None = None) -> aioboto3.Session:
    """Create an aioboto3 session with optional AWS profile.

    Args:
        profile: Optional AWS profile name to use

    Returns:
        aioboto3 Session
    """
    try:
        if profile:
            return aioboto3.Session(profile_name=profile)
        else:
            return aioboto3.Session()
    except Exception as e:
        raise RuntimeError(f"Failed to create aioboto3 session with profile '{profile}': {e}") from e


@click.group()
@click.option(
    "--s3-prefix",
    required=True,
    help="S3 prefix in format s3://bucket/prefix/ (e.g., s3://my-bucket/checkpoints/)",
)
@click.option(
    "--profile",
    help="AWS profile to use for authentication (optional, defaults to default profile or environment credentials)",
)
@click.pass_context
def cli(ctx: click.Context, s3_prefix: str, profile: str | None) -> None:
    """S3 Checkpoint Reader - Read LangGraph checkpoints from S3.

    This tool helps you read and inspect LangGraph checkpoints stored in Amazon S3.
    All output is in JSON format and sent to stdout.

    AWS Authentication:
        The tool uses standard AWS credential chain. You can specify a profile with --profile,
        or it will use environment variables, default profile, or IAM roles.

    Examples:
        s3-checkpoint list --s3-prefix s3://my-bucket/checkpoints/ --thread-id abc123
        s3-checkpoint dump --s3-prefix s3://my-bucket/checkpoints/ --thread-id abc123 --checkpoint-ns "" --checkpoint-id xyz789
        s3-checkpoint read --s3-prefix s3://my-bucket/checkpoints/ --thread-id abc123 --profile my-aws-profile
    """
    ctx.ensure_object(dict)

    # Parse S3 URI
    try:
        bucket_name, prefix = parse_s3_uri(s3_prefix)
        ctx.obj["bucket_name"] = bucket_name
        ctx.obj["prefix"] = prefix
        ctx.obj["profile"] = profile
    except ValueError as e:
        handle_error(e, 1)


@cli.command()
@click.option("--thread-id", required=True, help="Thread ID to list checkpoints for")
@click.pass_context
def list(ctx: click.Context, thread_id: str) -> None:
    """List all (checkpoint_ns, checkpoint_id) pairs for a thread.

    This command lists all available checkpoints for the specified thread ID,
    showing the checkpoint namespace and checkpoint ID for each one.

    Output format:

    \b
    {
      "thread_id": "thread123",
      "checkpoints": [
        {"checkpoint_ns": "", "checkpoint_id": "checkpoint1"},
        {"checkpoint_ns": "namespace1", "checkpoint_id": "checkpoint2"}
      ]
    }
    """
    try:
        click.echo(f"Listing checkpoints for thread '{thread_id}'...", err=True)
        session = create_aioboto3_session(ctx.obj["profile"])
        reader = S3CheckpointReader(ctx.obj["bucket_name"], ctx.obj["prefix"], session)
        checkpoints = reader.list_checkpoints(thread_id)

        output_data = {"thread_id": thread_id, "checkpoints": checkpoints}
        output_json(output_data)

    except RuntimeError as e:
        if "Failed to create aioboto3 session" in str(e):
            handle_error(e, 2)  # AWS credentials error
        elif "Failed to list checkpoints" in str(e):
            handle_error(e, 3)  # S3 access error
        else:
            handle_error(e, 4)  # Other runtime error
    except Exception as e:
        handle_error(f"Unexpected error: {e}", 5)


@cli.command()
@click.option("--thread-id", required=True, help="Thread ID")
@click.option("--checkpoint-ns", required=True, help="Checkpoint namespace (use empty string for default)")
@click.option("--checkpoint-id", required=True, help="Checkpoint ID")
@click.pass_context
def dump(ctx: click.Context, thread_id: str, checkpoint_ns: str, checkpoint_id: str) -> None:
    """Dump a specific checkpoint object.

    This command retrieves and displays the full checkpoint data, metadata,
    and pending writes for a specific checkpoint.

    Output format:

    \b
    {
      "thread_id": "thread123",
      "checkpoint_ns": "",
      "checkpoint_id": "checkpoint1",
      "checkpoint": { /* full checkpoint object */ },
      "metadata": { /* checkpoint metadata */ },
      "pending_writes": [ /* associated writes */ ]
    }
    """
    try:
        ns_display = f"'{checkpoint_ns}'" if checkpoint_ns else "default"
        click.echo(
            f"Retrieving checkpoint '{checkpoint_id}' from namespace {ns_display} in thread '{thread_id}'...", err=True
        )
        session = create_aioboto3_session(ctx.obj["profile"])
        reader = S3CheckpointReader(ctx.obj["bucket_name"], ctx.obj["prefix"], session)
        checkpoint_data = reader.dump_checkpoint(thread_id, checkpoint_ns, checkpoint_id)
        output_json(checkpoint_data)

    except RuntimeError as e:
        if "Failed to create aioboto3 session" in str(e):
            handle_error(e, 2)  # AWS credentials error
        elif "Checkpoint not found" in str(e):
            handle_error(e, 4)  # Checkpoint not found
        elif "Failed to get checkpoint" in str(e):
            handle_error(e, 3)  # S3 access error
        else:
            handle_error(e, 4)  # Other runtime error
    except Exception as e:
        handle_error(f"Unexpected error: {e}", 5)


@cli.command()
@click.option("--thread-id", required=True, help="Thread ID to read all checkpoints for")
@click.pass_context
def read(ctx: click.Context, thread_id: str) -> None:
    """Read all checkpoints with their objects for a thread.

    This command retrieves and displays all checkpoints for the specified thread,
    including their full checkpoint data, metadata, and pending writes.

    Output format:

    \b
    {
      "thread_id": "thread123",
      "checkpoints": [
        {
          "checkpoint_ns": "",
          "checkpoint_id": "checkpoint1",
          "checkpoint": { /* checkpoint object */ },
          "metadata": { /* metadata */ },
          "pending_writes": [ /* writes */ ]
        }
      ]
    }
    """
    try:
        session = create_aioboto3_session(ctx.obj["profile"])
        reader = S3CheckpointReader(ctx.obj["bucket_name"], ctx.obj["prefix"], session)
        all_checkpoints = reader.read_all_checkpoints(thread_id)

        output_data = {"thread_id": thread_id, "checkpoints": all_checkpoints}
        output_json(output_data)

    except RuntimeError as e:
        if "Failed to create aioboto3 session" in str(e):
            handle_error(e, 2)  # AWS credentials error
        elif "Failed to list checkpoints" in str(e):
            handle_error(e, 3)  # S3 access error
        else:
            handle_error(e, 4)  # Other runtime error
    except Exception as e:
        handle_error(f"Unexpected error: {e}", 5)


if __name__ == "__main__":
    # Run the CLI with an event loop so AsyncS3CheckpointSaver can work
    asyncio.run(cli())
