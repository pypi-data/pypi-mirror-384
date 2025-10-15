"""
Utility functions for managing environment variables and dotenv files with caching prevention.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv


class EnvManager:
    """
    Manages environment variables with proper caching prevention.
    """

    @staticmethod
    def clear_env_vars_from_file(env_file_path: Path) -> None:
        """
        Clear environment variables that exist in the specified .env file from os.environ.

        Args:
            env_file_path: Path to the .env file
        """
        if not env_file_path.exists():
            return

        with open(env_file_path, "r") as f:
            content = f.read()

        for line in content.splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key = line.split("=", 1)[0].strip()
                os.environ.pop(key, None)

    @staticmethod
    def write_env_file_safely(env_file_path: Path, content: str) -> None:
        """
        Write content to .env file with proper flushing and sync.

        Args:
            env_file_path: Path to the .env file
            content: Content to write
        """
        # Ensure parent directory exists
        env_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with proper flushing
        with open(env_file_path, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

    @staticmethod
    def load_env_with_retry(
        env_file_path: Path,
        max_retries: int = 3,
        retry_delay: float = 0.1,
        override: bool = True,
    ) -> bool:
        """
        Load .env file with retry mechanism to handle caching issues.

        Args:
            env_file_path: Path to the .env file
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            override: Whether to override existing environment variables

        Returns:
            bool: True if successfully loaded, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Small delay to ensure file system consistency
                if attempt > 0:
                    time.sleep(retry_delay)

                # Verify file exists and is readable
                if not env_file_path.exists():
                    raise FileNotFoundError(f".env file not found: {env_file_path}")

                # Read file content to verify it's accessible
                with open(env_file_path, "r") as f:
                    content = f.read()

                if not content.strip():
                    raise ValueError("Empty .env file")

                # Load environment variables
                success = load_dotenv(env_file_path, override=override)

                if success:
                    return True

            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(
                        f"Failed to load .env file after {max_retries} attempts: {e}"
                    )
                continue

        return False

    @staticmethod
    def update_env_file_safely(
        env_file_path: Path, new_content: str, clear_old_vars: bool = True
    ) -> None:
        """
        Safely update .env file with new content, handling caching issues.

        Args:
            env_file_path: Path to the .env file
            new_content: New content to write
            clear_old_vars: Whether to clear old environment variables
        """
        # Clear old environment variables if requested
        if clear_old_vars:
            EnvManager.clear_env_vars_from_file(env_file_path)

        # Write new content safely
        EnvManager.write_env_file_safely(env_file_path, new_content)

        # Load new environment variables with retry
        EnvManager.load_env_with_retry(env_file_path, override=True)
