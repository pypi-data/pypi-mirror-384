"""
Environment resolver utility that determines environment from CODEMIE_API_DOMAIN.

This module provides a robust way to resolve the environment based on the
API domain, eliminating the need for hardcoded ENV variables and preventing
configuration drift between domain and environment settings.
"""

import os
import re

from codemie_test_harness.tests.enums.environment import Environment


class EnvironmentResolver:
    """
    Resolves environment configuration based on CODEMIE_API_DOMAIN.

    Supported environments and their domain patterns:
    - prod: Production domains (*.lab.epam.com)
    - preview: Preview domains (*-preview.lab.epam.com)
    - localhost: Local development (localhost, 127.0.0.1)
    - azure: Azure sandbox environments (*-azure.eks-sandbox.*)
    - gcp: GCP sandbox environments (*-gcp.eks-sandbox.*)
    - aws: AWS sandbox environments (*-aws.eks-sandbox.*)
    - unknown: Any unrecognized domain
    """

    # Regex patterns for environment detection (order matters - more specific first)
    DOMAIN_PATTERNS = {
        # Production environments
        r"^https?://.*codemie\.lab\.epam\.com(/.*)?$": Environment.PRODUCTION,
        # Preview environments
        r"^https?://.*codemie-preview\.lab\.epam\.com(/.*)?$": Environment.PREVIEW,
        # Specific cloud sandbox environments
        r"^https?://.*codemie-azure\.eks-sandbox\.aws\.main\.edp\.projects\.epam\.com(/.*)?$": Environment.AZURE,
        r"^https?://.*codemie-gcp\.eks-sandbox\.aws\.main\.edp\.projects\.epam\.com(/.*)?$": Environment.GCP,
        r"^https?://.*codemie-aws\.eks-sandbox\.aws\.main\.edp\.projects\.epam\.com(/.*)?$": Environment.AWS,
        # Local development patterns
        r"^https?://localhost(:\d+)?(/.*)?$": Environment.LOCALHOST,
        r"^https?://127\.0\.0\.1(:\d+)?(/.*)?$": Environment.LOCALHOST,
    }

    @classmethod
    def get_environment(cls) -> Environment:
        """
        Get the current environment based on CODEMIE_API_DOMAIN.

        This is the main method that should be used throughout the codebase
        to replace os.getenv("ENV") calls.

        Returns:
            Environment: The resolved environment enum value

        Raises:
            ValueError: If CODEMIE_API_DOMAIN is not set
        """
        codemie_api_domain = os.getenv("CODEMIE_API_DOMAIN")

        if not codemie_api_domain:
            raise ValueError("CODEMIE_API_DOMAIN environment variable is not set")

        # Clean up the domain (remove trailing slashes)
        domain = codemie_api_domain.rstrip("/")

        # Try pattern matching (order matters - more specific patterns first)
        for pattern, environment in cls.DOMAIN_PATTERNS.items():
            if re.match(pattern, domain, re.IGNORECASE):
                return environment

        # If no match found, return 'unknown'
        return Environment.UNKNOWN

    @classmethod
    def is_production(cls) -> bool:
        """Check if current environment is production."""
        return cls.get_environment().is_production

    @classmethod
    def is_preview(cls) -> bool:
        """Check if current environment is preview."""
        return cls.get_environment().is_preview

    @classmethod
    def is_localhost(cls) -> bool:
        """Check if current environment is localhost."""
        return cls.get_environment().is_localhost

    @classmethod
    def is_sandbox(cls) -> bool:
        """Check if current environment is any sandbox environment."""
        return cls.get_environment().is_sandbox

    @classmethod
    def is_azure(cls) -> bool:
        """Check if current environment is Azure."""
        return cls.get_environment().is_azure

    @classmethod
    def is_gcp(cls) -> bool:
        """Check if current environment is GCP."""
        return cls.get_environment().is_gcp

    @classmethod
    def is_aws(cls) -> bool:
        """Check if current environment is AWS."""
        return cls.get_environment().is_aws


def get_environment() -> Environment:
    """
    Convenience function to get the current environment.

    This is the primary function that should replace os.getenv("ENV") throughout the codebase.

    Returns:
        Environment: The resolved environment enum value
    """
    return EnvironmentResolver.get_environment()
