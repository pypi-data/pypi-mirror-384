import json
import uuid
from pathlib import Path
from typing import Any

import click
import jwt
import requests
from docker.client import DockerClient

from tinybird.tb.modules.cli import cli
from tinybird.tb.modules.common import echo_json, update_cli
from tinybird.tb.modules.feedback_manager import FeedbackManager
from tinybird.tb.modules.local_common import (
    TB_CONTAINER_NAME,
    TB_LOCAL_ADDRESS,
    get_docker_client,
    get_existing_container_with_matching_env,
    start_tinybird_local,
)


def stop_tinybird_local(docker_client: DockerClient) -> None:
    """Stop the Tinybird container."""
    try:
        container = docker_client.containers.get(TB_CONTAINER_NAME)
        container.stop()
    except Exception:
        pass


def remove_tinybird_local(docker_client: DockerClient, persist_data: bool) -> None:
    """Remove the Tinybird container."""
    try:
        container = docker_client.containers.get(TB_CONTAINER_NAME)
        if persist_data or click.confirm(
            FeedbackManager.warning(
                message="△ This step will remove all your data inside Tinybird Local. Are you sure? [y/N]:"
            ),
            show_default=False,
            prompt_suffix="",
        ):
            container.remove(force=True)
    except Exception:
        pass


@cli.command()
def update() -> None:
    """Update Tinybird CLI to the latest version."""
    update_cli()


@cli.command(name="upgrade", hidden=True)
def upgrade() -> None:
    """Update Tinybird CLI to the latest version."""
    update_cli()


@cli.group()
@click.pass_context
def local(ctx: click.Context) -> None:
    """Manage the local Tinybird instance."""


@local.command()
def stop() -> None:
    """Stop Tinybird Local"""
    click.echo(FeedbackManager.highlight(message="» Shutting down Tinybird Local..."))
    docker_client = get_docker_client()
    stop_tinybird_local(docker_client)
    click.echo(FeedbackManager.success(message="✓ Tinybird Local stopped."))


@local.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check status of Tinybird Local"""
    docker_client = get_docker_client()
    container = get_existing_container_with_matching_env(docker_client, TB_CONTAINER_NAME, {})

    if container:
        status = container.status
        health = container.attrs.get("State", {}).get("Health", {}).get("Status")

        if status == "running" and health == "healthy":
            click.echo(FeedbackManager.success(message="✓ Tinybird Local is ready!"))
            click.echo(FeedbackManager.highlight(message="\n» Tinybird Local:"))
            from tinybird.tb.modules.info import get_local_info

            config = ctx.ensure_object(dict).get("config", {})
            get_local_info(config)
        elif status == "restarting" or (status == "running" and health == "starting"):
            click.echo(FeedbackManager.highlight(message="* Tinybird Local is starting..."))
        elif status == "removing":
            click.echo(FeedbackManager.highlight(message="* Tinybird Local is stopping..."))
        else:
            click.echo(
                FeedbackManager.info(message="✗ Tinybird Local is not running. Run 'tb local start' to start it")
            )
    else:
        click.echo(FeedbackManager.info(message="✗ Tinybird Local is not running. Run 'tb local start' to start it"))


@local.command()
def remove() -> None:
    """Remove Tinybird Local"""
    click.echo(FeedbackManager.highlight(message="» Removing Tinybird Local..."))
    docker_client = get_docker_client()
    remove_tinybird_local(docker_client, persist_data=False)
    click.echo(FeedbackManager.success(message="✓ Tinybird Local removed"))


@local.command()
@click.option(
    "--use-aws-creds",
    default=False,
    is_flag=True,
    help="Use local AWS credentials from your environment and pass them to the Tinybird docker container",
)
@click.option(
    "--volumes-path",
    default=None,
    help="Path to the volumes directory. If not provided, the container data won't be persisted.",
)
@click.option(
    "--skip-new-version",
    default=False,
    is_flag=True,
    help="Skip pulling the latest Tinybird Local image. Use directly your current local image.",
)
@click.option(
    "--user-token",
    default=None,
    envvar="TB_LOCAL_USER_TOKEN",
    help="User token to use for the Tinybird Local container.",
)
@click.option(
    "--workspace-token",
    default=None,
    envvar="TB_LOCAL_WORKSPACE_TOKEN",
    help="Workspace token to use for the Tinybird Local container.",
)
def start(
    use_aws_creds: bool, volumes_path: str, skip_new_version: bool, user_token: str, workspace_token: str
) -> None:
    """Start Tinybird Local"""
    if volumes_path is not None:
        absolute_path = Path(volumes_path).absolute()
        absolute_path.mkdir(parents=True, exist_ok=True)
        volumes_path = str(absolute_path)

    click.echo(FeedbackManager.highlight(message="» Starting Tinybird Local..."))
    docker_client = get_docker_client()
    start_tinybird_local(docker_client, use_aws_creds, volumes_path, skip_new_version, user_token, workspace_token)
    click.echo(FeedbackManager.success(message="✓ Tinybird Local is ready!"))


@local.command()
@click.option(
    "--use-aws-creds",
    default=False,
    is_flag=True,
    help="Use local AWS credentials from your environment and pass them to the Tinybird docker container",
)
@click.option(
    "--volumes-path",
    default=None,
    help="Path to the volumes directory. If not provided, the container data won't be persisted.",
)
@click.option(
    "--skip-new-version",
    default=False,
    is_flag=True,
    help="Skip pulling the latest Tinybird Local image. Use directly your current local image.",
)
@click.option(
    "--yes",
    default=False,
    is_flag=True,
    help="Skip the confirmation prompt. If provided, the container will be restarted without asking for confirmation.",
)
def restart(use_aws_creds: bool, volumes_path: str, skip_new_version: bool, yes: bool) -> None:
    """Restart Tinybird Local"""
    if volumes_path is not None:
        absolute_path = Path(volumes_path).absolute()
        absolute_path.mkdir(parents=True, exist_ok=True)
        volumes_path = str(absolute_path)

    click.echo(FeedbackManager.highlight(message="» Restarting Tinybird Local..."))
    docker_client = get_docker_client()
    persist_data = volumes_path is not None or yes
    remove_tinybird_local(docker_client, persist_data)
    click.echo(FeedbackManager.info(message="✓ Tinybird Local stopped"))
    start_tinybird_local(docker_client, use_aws_creds, volumes_path, skip_new_version)
    click.echo(FeedbackManager.success(message="✓ Tinybird Local is ready!"))


@local.command()
def version() -> None:
    """Show Tinybird Local version"""
    response = requests.get(f"{TB_LOCAL_ADDRESS}/version")
    click.echo(FeedbackManager.success(message=f"✓ Tinybird Local version: {response.text}"))


@local.command()
@click.pass_context
def generate_tokens(ctx: click.Context) -> None:
    """Generate static tokens for initializing Tinybird Local"""
    output = ctx.ensure_object(dict).get("output")
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    user_token_id = str(uuid.uuid4())
    workspace_token_id = str(uuid.uuid4())
    payload = {"u": user_id, "id": user_token_id, "host": None}
    user_token = generate_token(payload)
    payload = {"u": workspace_id, "id": workspace_token_id, "host": None}
    workspace_token = generate_token(payload)

    if output == "json":
        echo_json({"workspace_token": workspace_token, "user_token": user_token})
    else:
        click.echo(FeedbackManager.gray(message="Workspace token: ") + FeedbackManager.info(message=workspace_token))
        click.echo(FeedbackManager.gray(message="User token: ") + FeedbackManager.info(message=user_token))
        click.echo(FeedbackManager.success(message="✓ Tinybird Local tokens generated!"))


def generate_token(payload: dict[str, Any]) -> str:
    algo = jwt.algorithms.get_default_algorithms()["HS256"]
    msg = json.dumps(payload)
    msg_base64 = jwt.utils.base64url_encode(msg.encode())
    sign_key = algo.prepare_key("abcd")
    signature = algo.sign(msg_base64, sign_key)
    token = msg_base64 + b"." + jwt.utils.base64url_encode(signature)
    return "p." + token.decode()
