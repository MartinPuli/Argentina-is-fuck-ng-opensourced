"""State in SQLite, audit trail in ClickHouse.

SQLite holds purchases and attachments (the internal file). Every gate action is
also written as an event. Events go to ClickHouse when CLICKHOUSE_HOST is set,
otherwise to a local SQLite table with the same columns, so the demo runs offline.
"""

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("GATE_DB", Path(__file__).resolve().parents[2] / "gate.db"))

SCHEMA = """
create table if not exists purchases (
    id integer primary key, office text, procedure text, item text, amount real,
    created_at real
);
create table if not exists attachments (
    id integer primary key, purchase_id integer, filename text, sha256 text, pdf blob,
    decision text, reasons text, findings text, model text, agent text,
    reviewed_by text, reviewed_at real, review_note text, created_at real
);
create table if not exists events (
    ts text, event text, office text, purchase_id integer, attachment_id integer,
    filename text, decision text, kinds text, actor text, latency_ms real
);
"""


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


class Events:
    def __init__(self) -> None:
        self.ch = None
        self.lock = threading.Lock()  # one ClickHouse client is shared by request and agent threads
        if os.getenv("CLICKHOUSE_HOST"):
            import clickhouse_connect

            self.ch = clickhouse_connect.get_client(
                host=os.environ["CLICKHOUSE_HOST"],
                port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
                username=os.getenv("CLICKHOUSE_USER", "default"),
                password=os.getenv("CLICKHOUSE_PASSWORD", ""),
                secure=os.getenv("CLICKHOUSE_SECURE", "1") == "1",
                autogenerate_session_id=False,
            )
            self.ch.command(
                """create table if not exists gate_events (
                    ts DateTime64(3, 'UTC'), event LowCardinality(String),
                    office LowCardinality(String), purchase_id UInt32, attachment_id UInt32,
                    filename String, decision LowCardinality(String), kinds Array(String),
                    actor String, latency_ms Float32
                ) engine = MergeTree order by (office, ts)"""
            )

    @property
    def backend(self) -> str:
        return "ClickHouse" if self.ch else "local SQLite"

    def log(self, event: str, office: str, purchase_id: int, attachment_id: int = 0,
            filename: str = "", decision: str = "", kinds: list[str] | None = None,
            actor: str = "gate", latency_ms: float = 0.0) -> None:
        now = datetime.now(timezone.utc)
        kinds = kinds or []
        if self.ch:
            with self.lock:
                self.ch.insert(
                    "gate_events",
                    [[now, event, office, purchase_id, attachment_id, filename, decision, kinds, actor, latency_ms]],
                    column_names=["ts", "event", "office", "purchase_id", "attachment_id",
                                  "filename", "decision", "kinds", "actor", "latency_ms"],
                )
            return
        with db() as con:
            con.execute(
                "insert into events values (?,?,?,?,?,?,?,?,?,?)",
                (now.isoformat(), event, office, purchase_id, attachment_id, filename,
                 decision, json.dumps(kinds), actor, latency_ms),
            )

    def stats(self) -> dict:
        """Numbers for the dashboard. Same questions on both backends."""
        if self.ch:
            with self.lock:
                return self._ch_stats()
        return self._sqlite_stats()

    def _ch_stats(self) -> dict:
        q = self.ch.query
        by_office = q(
            "select office, countIf(decision='public'), countIf(decision='hold'), "
            "countIf(decision='withheld') from gate_events where event='decision' "
            "group by office order by office"
        ).result_rows
        kinds = q(
            "select k, count() c from gate_events array join kinds as k "
            "where event='decision' group by k order by c desc limit 10"
        ).result_rows
        latency = q(
            "select round(quantile(0.5)(latency_ms)), round(max(latency_ms)), count() "
            "from gate_events where event='decision'"
        ).result_rows[0]
        reviews = q(
            "select actor, decision, filename, ts from gate_events "
            "where event in ('approved','rejected') order by ts desc limit 10"
        ).result_rows
        total = q("select count() from gate_events").result_rows[0][0]
        return {"by_office": by_office, "kinds": kinds, "latency": latency,
                "reviews": reviews, "total": total, "backend": self.backend}

    def _sqlite_stats(self) -> dict:
        with db() as con:
            by_office = [tuple(r) for r in con.execute(
                "select office, sum(decision='public'), sum(decision='hold'), "
                "sum(decision='withheld') from events where event='decision' "
                "group by office order by office")]
            counts: dict[str, int] = {}
            for (k,) in con.execute("select kinds from events where event='decision'"):
                for kind in json.loads(k):
                    counts[kind] = counts.get(kind, 0) + 1
            kinds = sorted(counts.items(), key=lambda kv: -kv[1])[:10]
            lat = sorted(r[0] for r in con.execute(
                "select latency_ms from events where event='decision'"))
            latency = (round(lat[len(lat) // 2]) if lat else 0, round(lat[-1]) if lat else 0, len(lat))
            reviews = [tuple(r) for r in con.execute(
                "select actor, decision, filename, ts from events "
                "where event in ('approved','rejected') order by ts desc limit 10")]
            total = con.execute("select count(*) from events").fetchone()[0]
        return {"by_office": by_office, "kinds": kinds, "latency": latency,
                "reviews": reviews, "total": total, "backend": self.backend}


def now() -> float:
    return time.time()
