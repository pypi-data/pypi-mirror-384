import pytest
import polarion_rest_client as hl


def test_version_exposed():
    assert isinstance(hl.__version__, str)


def test_client_requires_auth():
    # constructing without token or username+password must fail
    with pytest.raises(ValueError):
        hl.PolarionClient(base_url="https://example.invalid")


def test_get_env_vars_and_client(monkeypatch):
    # Missing URL should fail
    monkeypatch.delenv("POLARION_TEST_URL", raising=False)
    monkeypatch.delenv("POLARION_TOKEN", raising=False)
    monkeypatch.delenv("POLARION_USERNAME", raising=False)
    monkeypatch.delenv("POLARION_PASSWORD", raising=False)

    with pytest.raises(ValueError):
        hl.get_env_vars(base_url_var="POLARION_TEST_URL")

    # Token path
    monkeypatch.setenv("POLARION_TEST_URL", "https://example.invalid")
    monkeypatch.setenv("POLARION_TOKEN", "dummy-token")

    kwargs = hl.get_env_vars(base_url_var="POLARION_TEST_URL")
    pc = hl.PolarionClient(**kwargs)
    assert pc.gen is not None
    assert pc.base_url.endswith("/polarion/rest/v1")

    # Basic auth path
    monkeypatch.setenv("POLARION_TOKEN", "")
    monkeypatch.setenv("POLARION_USERNAME", "u")
    monkeypatch.setenv("POLARION_PASSWORD", "p")

    kwargs = hl.get_env_vars(base_url_var="POLARION_TEST_URL")
    pc = hl.PolarionClient(**kwargs)
    assert pc.gen is not None
