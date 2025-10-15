import dotenv
import pytest

import polarion_rest_client as prc


@pytest.fixture
def dotenv_test_env():
    if not dotenv.load_dotenv(".env.test"):
        pytest.skip("Polarion env not configured for integration tests")


@pytest.fixture
def polarion_test_client(dotenv_test_env):
    try:
        return prc.PolarionClient(**prc.get_env_vars())
    except Exception as e:
        raise ValueError(f"Invalid test env configuration: {e}") from e
