"""Client factory utilities for tests."""

from codemie_sdk import CodeMieClient
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager


def get_client():
    """Create a test client instance."""
    # Use unified credentials manager for all client credentials
    return CodeMieClient(
        auth_server_url=CredentialsManager.get_parameter("AUTH_SERVER_URL", ""),
        auth_client_id=CredentialsManager.get_parameter("AUTH_CLIENT_ID", ""),
        auth_client_secret=CredentialsManager.get_parameter("AUTH_CLIENT_SECRET", ""),
        auth_realm_name=CredentialsManager.get_parameter("AUTH_REALM_NAME", ""),
        codemie_api_domain=CredentialsManager.get_parameter("CODEMIE_API_DOMAIN"),
        verify_ssl=CredentialsManager.get_parameter("VERIFY_SSL", "false").lower()
        == "true",
        username=CredentialsManager.get_parameter("AUTH_USERNAME"),
        password=CredentialsManager.get_parameter("AUTH_PASSWORD"),
    )
