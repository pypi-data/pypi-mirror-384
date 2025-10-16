"""Main CLI entry point for CodeMie Test Harness.

Thin entry point: registers commands and wires common options.
"""

from __future__ import annotations

import os
from typing import Optional

import click

from .constants import (
    CONTEXT_SETTINGS,
    KEY_MARKS,
    KEY_XDIST_N,
    KEY_RERUNS,
    KEY_COUNT,
    KEY_TIMEOUT,
    KEY_AUTH_SERVER_URL,
    KEY_AUTH_CLIENT_ID,
    KEY_AUTH_CLIENT_SECRET,
    KEY_AUTH_REALM_NAME,
    KEY_CODEMIE_API_DOMAIN,
    KEY_AUTH_USERNAME,
    KEY_AUTH_PASSWORD,
    DEFAULT_MARKS,
    DEFAULT_XDIST_N,
    DEFAULT_RERUNS,
    DEFAULT_TIMEOUT,
)
from .utils import get_config_value, ensure_env_from_config
from .runner import run_pytest
from .commands.config_cmd import config_cmd
from .commands.run_cmd import run_cmd
from .commands.assistant_cmd import assistant_cmd
from .commands.workflow_cmd import workflow_cmd
from .commands.marks_cmd import marks_cmd


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--marks",
    envvar=KEY_MARKS,
    help="Pytest -m expression, default from config or 'smoke'",
)
@click.option(
    "-n", "workers", envvar=KEY_XDIST_N, type=int, help="Number of xdist workers (-n)"
)
@click.option(
    "--reruns", envvar=KEY_RERUNS, type=int, help="Number of reruns for flaky tests"
)
@click.option(
    "--count",
    envvar=KEY_COUNT,
    type=int,
    help="Number of times to repeat each test (requires pytest-repeat)",
)
@click.option(
    "--timeout",
    envvar=KEY_TIMEOUT,
    type=int,
    help="Per-test timeout in seconds (default: 300)",
)
@click.option("--auth-server-url", envvar=KEY_AUTH_SERVER_URL, help="Auth server url")
@click.option("--auth-client-id", envvar=KEY_AUTH_CLIENT_ID, help="Auth client id")
@click.option(
    "--auth-client-secret", envvar=KEY_AUTH_CLIENT_SECRET, help="Auth client secret"
)
@click.option("--auth-realm-name", envvar=KEY_AUTH_REALM_NAME, help="Auth realm name")
@click.option("--auth-username", envvar=KEY_AUTH_USERNAME, help="Auth username")
@click.option("--auth-password", envvar=KEY_AUTH_PASSWORD, help="Auth password")
@click.option(
    "--api-domain", envvar=KEY_CODEMIE_API_DOMAIN, help="CodeMie API domain URL"
)
# Integration credentials are set via 'codemie-test-harness config set' command
@click.pass_context
def cli(
    ctx: click.Context,
    marks: Optional[str],
    workers: Optional[int],
    reruns: Optional[int],
    count: Optional[int],
    timeout: Optional[int],
    auth_server_url: Optional[str],
    auth_client_id: Optional[str],
    auth_client_secret: Optional[str],
    auth_realm_name: Optional[str],
    auth_username: Optional[str],
    auth_password: Optional[str],
    api_domain: Optional[str],
):
    """CodeMie Test Harness CLI.

    Without subcommand it will run pytest using configured defaults.

    Integration credentials should be set using:
      codemie-test-harness config set KEY VALUE

    Use 'codemie-test-harness config vars' to see all available credentials.
    """
    ctx.ensure_object(dict)

    # Resolve options using env -> config -> defaults
    resolved_marks = marks or get_config_value(KEY_MARKS, DEFAULT_MARKS)
    resolved_workers = (
        workers
        if workers is not None
        else int(get_config_value(KEY_XDIST_N, str(DEFAULT_XDIST_N)))
    )
    resolved_reruns = (
        reruns
        if reruns is not None
        else int(get_config_value(KEY_RERUNS, str(DEFAULT_RERUNS)))
    )
    resolved_count = (
        count
        if count is not None
        else (int(get_config_value(KEY_COUNT)) if get_config_value(KEY_COUNT) else None)
    )
    resolved_timeout = (
        timeout
        if timeout is not None
        else int(get_config_value(KEY_TIMEOUT, str(DEFAULT_TIMEOUT)))
    )

    # Ensure env vars. CLI args override env/config.
    provided = {
        # auth/api
        KEY_AUTH_SERVER_URL: auth_server_url,
        KEY_AUTH_CLIENT_ID: auth_client_id,
        KEY_AUTH_CLIENT_SECRET: auth_client_secret,
        KEY_AUTH_USERNAME: auth_username,
        KEY_AUTH_PASSWORD: auth_password,
        KEY_AUTH_REALM_NAME: auth_realm_name,
        KEY_CODEMIE_API_DOMAIN: api_domain,
    }
    for k, v in provided.items():
        if v is not None and v != "":
            os.environ[k] = str(v)
    # populate any missing values from saved config
    ensure_env_from_config()

    ctx.obj.update(
        dict(
            marks=resolved_marks,
            workers=resolved_workers,
            reruns=resolved_reruns,
            count=resolved_count,
            timeout=resolved_timeout,
        )
    )

    # default behavior
    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        run_pytest(
            resolved_workers,
            resolved_marks,
            resolved_reruns,
            resolved_count,
            resolved_timeout,
        )


# Register subcommands
cli.add_command(config_cmd)
cli.add_command(run_cmd)
cli.add_command(assistant_cmd)
cli.add_command(workflow_cmd)
cli.add_command(marks_cmd)


if __name__ == "__main__":  # pragma: no cover
    cli()
