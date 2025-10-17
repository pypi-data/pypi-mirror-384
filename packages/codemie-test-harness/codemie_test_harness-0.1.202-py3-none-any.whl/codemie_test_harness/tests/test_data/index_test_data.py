from dataclasses import dataclass
from typing import List

import pytest

from codemie_test_harness.tests.utils.env_resolver import get_environment
from codemie_test_harness.tests.enums.environment import Environment


@dataclass
class EmbeddingData:
    """Data class to store Embedding models."""

    model_type: str
    environments: List[Environment]


MODELS = [
    EmbeddingData("titan", Environment.get_aws_environments()),
    EmbeddingData("gecko", Environment.get_gcp_environments()),
    EmbeddingData("ada-002", Environment.get_azure_environments()),
]


def generate_test_data():
    """Generate pytest parameters for Embedding models"""
    env = get_environment()
    test_data = []

    for model in MODELS:
        test_data.append(
            pytest.param(
                model.model_type,
                marks=pytest.mark.skipif(
                    env not in model.environments,
                    reason=f"Skip on non {'/'.join(str(env) for env in model.environments[:-1])} envs",
                ),
            )
        )

    return test_data


index_test_data = generate_test_data()
