import os

import pytest

# gate/.env is loaded when gate.app is imported, and load_dotenv keeps variables that are already set.
# Blank the deployment settings first so a developer's live keys and flags never reach the offline suite.
for _name in ("AKASHML_API_KEY", "AKASHML_MODEL", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST",
              "CLICKHOUSE_USER", "CLICKHOUSE_PASSWORD", "GATE_OPEN_DEMO", "GATE_AUTONOMOUS", "SENSO_API_KEY"):
    os.environ[_name] = ""


@pytest.fixture(autouse=True)
def no_live_senso(monkeypatch):
    """A developer's gate/.env key must never turn the offline suite into live Senso calls."""
    monkeypatch.delenv("SENSO_API_KEY", raising=False)
