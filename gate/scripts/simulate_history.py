"""Fill ClickHouse with one year of SIMULATED gate telemetry.

Every row is synthetic and flagged simulated = 1. Nothing here comes from a real
PAMI system. The office names below are plausible UGL names for the demo, not an
official list.

The rows are generated server-side by a single INSERT ... SELECT FROM numbers(N),
so nothing is uploaded from this machine. The script is idempotent: it truncates
the table first.

    uv run python scripts/simulate_history.py [--env path/to/.env] [--rows 1000000]
"""

import argparse
import os
import time
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv

TABLE = "gate_events_sim"

# Plausible UGL names (not an official list), with a relative volume weight.
OFFICES = [
    ("UGL I La Plata", 6), ("UGL II Corrientes", 3), ("UGL III Córdoba", 5),
    ("UGL IV Mendoza", 4), ("UGL V San Martín", 4), ("UGL VI Capital Federal", 10),
    ("UGL VII La Pampa", 2), ("UGL VIII Morón", 5), ("UGL IX Rosario", 5),
    ("UGL X Lanús", 6), ("UGL XI Mar del Plata", 4), ("UGL XII Salta", 3),
    ("UGL XIII Chaco", 3), ("UGL XIV Entre Ríos", 3), ("UGL XV Neuquén", 2),
    ("UGL XVI Bahía Blanca", 3), ("UGL XVII Tucumán", 4), ("UGL XVIII Santiago del Estero", 2),
    ("UGL XIX Misiones", 3), ("UGL XX San Juan", 2), ("UGL XXI Junín", 2),
    ("UGL XXII Luján", 2), ("UGL XXIII Jujuy", 2), ("UGL XXIV Catamarca", 1),
    ("UGL XXV La Rioja", 1), ("UGL XXVI Formosa", 2), ("UGL XXVII Chubut", 2),
    ("UGL XXVIII Santa Cruz", 1), ("UGL XXIX Río Negro", 2), ("UGL XXX Chivilcoy", 2),
    ("UGL XXXI San Luis", 2), ("UGL XXXII Tierra del Fuego", 1), ("UGL XXXIII Quilmes", 4),
    ("UGL XXXIV Concordia", 2), ("UGL XXXV Azul", 2),
]
# Offices whose simulated upload habits are clearly riskier, so the dashboard has a story.
RISKY = ["UGL XIII Chaco", "UGL XIX Misiones", "UGL XXVI Formosa", "UGL X Lanús"]

KINDS = ["dni", "person_cuil", "affiliate_number", "birth_date", "home_address", "id_document",
         "disability_cert", "icd10", "health_terms", "model_context", "model_image"]
# Per-kind probability (per mille) of appearing in a file, by decision.
PROBS = {
    "cleaned":  [550, 450, 400, 250, 300, 0, 0, 0, 0, 60, 0],
    "withheld": [250, 200, 300, 150, 100, 350, 300, 400, 450, 120, 150],
    "hold":     [80, 60, 120, 40, 40, 60, 50, 100, 300, 450, 300],
}
FALLBACK = {"cleaned": ["dni", "person_cuil", "affiliate_number"],
            "withheld": ["id_document", "disability_cert", "icd10"],
            "hold": ["model_context", "model_image", "health_terms"]}
FILES = ["pliego", "orden_compra", "factura", "acta_apertura", "informe_tecnico",
         "dictamen", "nota_pedido", "presupuesto", "constancia", "anexo"]


def lit(values) -> str:
    return "[" + ",".join(f"'{v}'" if isinstance(v, str) else str(v) for v in values) + "]"


def insert_sql(rows: int) -> str:
    names, weights = zip(*OFFICES)
    return f"""
insert into {TABLE} (ts, event, office, purchase_id, attachment_id, filename, decision,
                     kinds, actor, latency_ms, policy_version, simulated)
with
    {lit(names)} as offices,
    arrayCumSum({lit(weights)}) as cum,
    {lit(RISKY)} as risky,
    {lit(KINDS)} as all_kinds
select
    ts, event, office, purchase_id, attachment_id, filename, decision,
    if(decision = 'public', [], if(empty(picked), [fallback[1 + h5 % 3]], picked)) as kinds,
    if(event in ('approved', 'rejected'), concat('reviewer-', leftPad(toString(1 + h6 % 12), 2, '0')), 'gate') as actor,
    toFloat32(if(event = 'decision', 180 + h7 % 650 + if(h7 % 100 < 4, h6 % 4000, 0), 0)) as latency_ms,
    multiIf(ts < now() - interval 7 month, 'v1', ts < now() - interval 2 month, 'v2', 'v3') as policy_version,
    1 as simulated
from (
    select
        number as n,
        cityHash64(n, 1) as h1, cityHash64(n, 2) as h2, cityHash64(n, 3) as h3,
        cityHash64(n, 4) as h4, cityHash64(n, 5) as h5, cityHash64(n, 6) as h6,
        cityHash64(n, 7) as h7,
        -- volume grows over the year: more rows near now
        toDateTime64(now() - toIntervalSecond(toUInt32(365 * 86400 * (1 - sqrt((h1 % 1000000) / 1e6)))), 3, 'UTC') as ts,
        offices[arrayFirstIndex(c -> c > h2 % cum[-1], cum)] as office,
        multiIf(h4 % 1000 < 900, 'decision', h4 % 1000 < 950, 'submitted', h4 % 1000 < 970, 'cleaned_copy',
                h4 % 1000 < 990, 'approved', 'rejected') as event,
        if(has(risky, office), 0.52, 0.27) as unsafe_rate,
        (h3 % 100000) / 1e5 as u,
        multiIf(u >= unsafe_rate, 'public', u < unsafe_rate * 0.40, 'cleaned',
                u < unsafe_rate * 0.733, 'withheld', 'hold') as decision,
        multiIf(decision = 'cleaned', {lit(PROBS['cleaned'])},
                decision = 'withheld', {lit(PROBS['withheld'])}, {lit(PROBS['hold'])}) as probs,
        multiIf(decision = 'cleaned', {lit(FALLBACK['cleaned'])},
                decision = 'withheld', {lit(FALLBACK['withheld'])}, {lit(FALLBACK['hold'])}) as fallback,
        arrayFilter((k, i) -> cityHash64(n, 100 + i) % 1000 < probs[i], all_kinds, arrayEnumerate(all_kinds)) as picked,
        100000 + intDiv(n, 3) as purchase_id,
        toUInt32(n + 1) as attachment_id,
        concat({lit(FILES)}[1 + h5 % {len(FILES)}], '_', toString(purchase_id), '.pdf') as filename
    from numbers({rows})
)"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--env", default=str(Path(__file__).resolve().parents[1] / ".env"))
    parser.add_argument("--rows", type=int, default=1_000_000)
    args = parser.parse_args()
    load_dotenv(args.env)
    if not os.getenv("CLICKHOUSE_HOST"):
        raise SystemExit("CLICKHOUSE_HOST is not set; nothing to simulate into.")
    ch = clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "1") == "1",
        autogenerate_session_id=False,
        send_receive_timeout=600,
    )
    ch.command(f"""create table if not exists {TABLE} (
        ts DateTime64(3, 'UTC'), event LowCardinality(String),
        office LowCardinality(String), purchase_id UInt32, attachment_id UInt32,
        filename String, decision LowCardinality(String), kinds Array(String),
        actor String, latency_ms Float32,
        policy_version LowCardinality(String), simulated UInt8 default 1
    ) engine = MergeTree order by (office, ts)
    comment 'SIMULATED gate telemetry for the demo. Not real PAMI data.'""")
    ch.command(f"truncate table {TABLE}")
    start = time.perf_counter()
    ch.command(insert_sql(args.rows))
    elapsed = time.perf_counter() - start
    count = ch.query(f"select count() from {TABLE}").result_rows[0][0]
    print(f"{count:,} simulated rows in {TABLE}; insert took {elapsed:.2f} s")


if __name__ == "__main__":
    main()
