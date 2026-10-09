import pytest


@pytest.fixture(autouse=True)
def no_live_senso(monkeypatch):
    """A developer's gate/.env key must never turn the offline suite into live Senso calls."""
    monkeypatch.delenv("SENSO_API_KEY", raising=False)
