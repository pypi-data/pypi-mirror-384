import os
import random
import string
from pathlib import Path

from dotenv import load_dotenv

from codemie_test_harness.cli.runner import resolve_tests_path_and_root
from codemie_test_harness.tests.utils.credentials_manager import CredentialsManager

_, root_dir = resolve_tests_path_and_root()
env_file_path = Path(root_dir) / ".env"

# Load initial .env file
load_dotenv(env_file_path)

LANGFUSE_TRACES_ENABLED = (
    os.getenv("LANGFUSE_TRACES_ENABLED", "false").lower() == "true"
)

PROJECT = os.getenv("PROJECT_NAME", "codemie")
TEST_USER = os.getenv("TEST_USER_FULL_NAME", "Test User")
GITHUB_URL = CredentialsManager.get_parameter("GITHUB_URL", "https://github.com")

autotest_entity_prefix = (
    f"{''.join(random.choice(string.ascii_lowercase) for _ in range(3))}_"
)
