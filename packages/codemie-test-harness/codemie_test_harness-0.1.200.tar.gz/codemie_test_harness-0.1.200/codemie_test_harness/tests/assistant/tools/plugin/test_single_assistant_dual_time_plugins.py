"""
This test verifies that a single assistant can have multiple instances of the same
MCP server plugin running with different configurations under the same plugin-key.
"""

import json
import os
import subprocess
import uuid
from pathlib import Path
from time import sleep
from typing import Tuple, List

import pytest

from codemie_test_harness.tests.enums.tools import Toolkit, McpServerTime
from codemie_sdk.models.integration import CredentialTypes
from codemie_test_harness.tests.conftest import cleanup_plugin_process
from codemie_test_harness.tests.test_data.plugin_tools_test_data import (
    dual_time_plugin_test_data,
)
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager
from codemie_test_harness.tests.utils.base_utils import assert_tool_triggered


CACHE_DIR = Path.home() / ".cache" / "uv" / "archive-v0"
SERVERS_JSON_PATH = "lib/python3.12/site-packages/toolkits/mcp/servers.json"
CODEMIE_PLUGINS_PATH = "bin/codemie-plugins"
PLUGIN_INIT_DELAY = 15

TIME_CONFIGS = {
    "time-kyiv": {"timezone": "Europe/Kiev", "label": "time-kyiv"},
    "time-tokyo": {"timezone": "Asia/Tokyo", "label": "time-tokyo"},
}


def find_cache_paths() -> Tuple[Path, Path]:
    """Find required cache paths for servers.json and codemie-plugins."""
    for cache_subdir in CACHE_DIR.glob("*"):
        if not cache_subdir.is_dir():
            continue

        servers_json = cache_subdir / SERVERS_JSON_PATH
        codemie_plugins = cache_subdir / CODEMIE_PLUGINS_PATH

        if servers_json.exists() and codemie_plugins.exists():
            return servers_json, codemie_plugins

    raise FileNotFoundError("Required cache files not found")


def configure_mcp_servers(servers_json_path: Path) -> None:
    """Configure MCP servers in servers.json."""
    with open(servers_json_path, "r+") as f:
        config = json.load(f)
        mcp_servers = config.get("mcpServers", {})

        for server_name, server_config in TIME_CONFIGS.items():
            if server_name not in mcp_servers:
                mcp_servers[server_name] = {
                    "command": "uvx",
                    "args": [
                        "mcp-server-time",
                        f"--local-timezone={server_config['timezone']}",
                    ],
                }

        f.seek(0)
        json.dump(config, f, indent=2)
        f.truncate()


def create_plugin_process(
    server_name: str, plugin_key: str, codemie_plugins_path: Path
) -> subprocess.Popen:
    """Create a plugin process for given server configuration."""
    config = TIME_CONFIGS[server_name]

    env = os.environ.copy()
    env.update(
        {"PLUGIN_LABEL": config["label"], "PLUGIN_EXPERIMENTAL_PROTOCOL": "true"}
    )

    command = [
        str(codemie_plugins_path),
        "--plugin-key",
        plugin_key,
        "--plugin-engine-uri",
        CredentialsManager.get_parameter("NATS_URL"),
        "mcp",
        "run",
        "-s",
        server_name,
        "-e",
        f"{server_name}=PLUGIN_LABEL",
    ]

    return subprocess.Popen(command, env=env)


def cleanup_processes(processes: List[subprocess.Popen]) -> None:
    """Clean up all managed processes."""
    for process in processes:
        cleanup_plugin_process(process)


@pytest.fixture(scope="module")
def dual_time_plugins(integration_utils):
    """Create two time plugin instances with different configurations."""
    plugin_key = str(uuid.uuid4())
    processes = []

    # Setup integration
    credential_values = CredentialsManager.plugin_credentials(plugin_key)
    settings = integration_utils.create_integration(
        credential_type=CredentialTypes.PLUGIN, credential_values=credential_values
    )

    # Download codemie-plugins and wait for completion
    download_process = subprocess.Popen(["uvx", "codemie-plugins"])
    processes.append(download_process)

    return_code = download_process.wait()
    if return_code != 0:
        raise RuntimeError(
            f"Failed to download codemie-plugins, exit code: {return_code}"
        )

    # Find paths and configure servers
    servers_json_path, codemie_plugins_path = find_cache_paths()
    configure_mcp_servers(servers_json_path)

    # Start plugin processes for each time config
    for server_name in TIME_CONFIGS.keys():
        process = create_plugin_process(server_name, plugin_key, codemie_plugins_path)
        processes.append(process)

    # Wait for plugin initialization
    sleep(PLUGIN_INIT_DELAY)

    yield settings
    cleanup_processes(processes)


@pytest.mark.assistant
@pytest.mark.mcp
@pytest.mark.plugin
@pytest.mark.api
@pytest.mark.parametrize(
    "prompt,expected_response",
    dual_time_plugin_test_data,
    ids=["Get Tools Available", "Get Kyiv time", "Get Tokyo time"],
)
def test_single_assistant_dual_time_plugins(
    dual_time_plugins,
    assistant_utils,
    assistant,
    similarity_check,
    prompt,
    expected_response,
):
    assistant_instance = assistant(
        Toolkit.PLUGIN, Toolkit.PLUGIN, settings=dual_time_plugins
    )

    response, triggered_tools = assistant_utils.ask_assistant(
        assistant_instance, prompt, minimal_response=False
    )

    if "tools" in prompt.lower():
        pass
    else:
        assert_tool_triggered(McpServerTime.GET_CURRENT_TIME, triggered_tools)

    similarity_check.check_similarity(response, expected_response)
