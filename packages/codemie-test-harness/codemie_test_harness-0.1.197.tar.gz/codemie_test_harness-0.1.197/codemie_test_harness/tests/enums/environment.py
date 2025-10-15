"""
Environment enumeration for CodeMie test harness.

This enum defines all supported environments for the CodeMie platform,
providing type safety and preventing typos in environment checks.
"""

from enum import Enum
from typing import List


class Environment(Enum):
    """
    Enumeration of supported CodeMie environments.

    Each environment corresponds to a specific deployment of the CodeMie platform
    with its own domain patterns and configuration requirements.
    """

    PRODUCTION = "prod"
    PREVIEW = "preview"
    LOCALHOST = "localhost"
    AZURE = "azure"
    GCP = "gcp"
    AWS = "aws"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return the string value of the environment."""
        return self.value

    @property
    def is_production(self) -> bool:
        """Check if this is the production environment."""
        return self == Environment.PRODUCTION

    @property
    def is_preview(self) -> bool:
        """Check if this is the preview environment."""
        return self == Environment.PREVIEW

    @property
    def is_localhost(self) -> bool:
        """Check if this is the localhost environment."""
        return self == Environment.LOCALHOST

    @property
    def is_sandbox(self) -> bool:
        """Check if this is any sandbox environment (azure, gcp, aws)."""
        return self in (Environment.AZURE, Environment.GCP, Environment.AWS)

    @property
    def is_azure(self) -> bool:
        """Check if this is the Azure sandbox environment."""
        return self == Environment.AZURE

    @property
    def is_gcp(self) -> bool:
        """Check if this is the GCP sandbox environment."""
        return self == Environment.GCP

    @property
    def is_aws(self) -> bool:
        """Check if this is the AWS sandbox environment."""
        return self == Environment.AWS

    @classmethod
    def get_all_sandbox_environments(cls) -> List["Environment"]:
        """Get all sandbox environments as enum values."""
        return [cls.AZURE, cls.GCP, cls.AWS]

    @classmethod
    def get_all_environments(cls) -> List["Environment"]:
        """Get all available environments."""
        return list(cls)

    @classmethod
    def get_azure_environments(cls) -> List["Environment"]:
        """Get environments where Azure services are available.

        Returns:
            List of Environment enums: [PREVIEW, AZURE, LOCALHOST]
        """
        return [cls.PREVIEW, cls.AZURE, cls.LOCALHOST, cls.PRODUCTION]

    @classmethod
    def get_gcp_environments(cls) -> List["Environment"]:
        """Get environments where GCP services are available.

        Returns:
            List of Environment enums: [PREVIEW, GCP, LOCALHOST]
        """
        return [cls.PREVIEW, cls.GCP, cls.LOCALHOST, cls.PRODUCTION]

    @classmethod
    def get_aws_environments(cls) -> List["Environment"]:
        """Get environments where AWS services are available.

        Returns:
            List of Environment enums: [PREVIEW, AWS, LOCALHOST]
        """
        return [cls.PREVIEW, cls.AWS, cls.LOCALHOST, cls.PRODUCTION]
