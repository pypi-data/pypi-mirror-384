import pytest

from erad.constants import SUPPORTED_MODELS


@pytest.mark.parametrize("disaster_model", SUPPORTED_MODELS)
def test_examples(disaster_model):
    disaster_model.example()
