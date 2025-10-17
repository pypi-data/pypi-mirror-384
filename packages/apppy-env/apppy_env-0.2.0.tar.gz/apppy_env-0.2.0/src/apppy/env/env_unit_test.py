import pytest

from apppy.env import Env


def test_find_secrets_dir_for_ci():
    env = Env.load(name="ci")
    secrets_dir = Env.find_secrets_dir(env)

    assert secrets_dir.exists() is True
    assert str(secrets_dir).endswith(
        ".github/ci/secrets"
    ), f"Unexpected secrets dir for ci: {secrets_dir}"


def test_find_secrets_dir_for_test():
    env = Env.load(name="test_find_secrets_dir_for_test")
    secrets_dir = Env.find_secrets_dir(env)

    assert secrets_dir.exists() is True
    assert str(secrets_dir).endswith(
        ".github/ci/secrets"
    ), f"Unexpected secrets dir for test: {secrets_dir}"


def test_find_secrets_dir(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "dummy")

    env = Env.load(name="dummy")
    secrets_dir = Env.find_secrets_dir(env)

    assert secrets_dir.exists() is True
    assert str(secrets_dir).endswith(
        "src/apppy/env/.secrets/dummy"
    ), f"Unexpected secrets dir found: {secrets_dir}"
