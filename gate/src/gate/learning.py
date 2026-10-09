"""Bounded, literal incident lessons; activation remains a staff decision.

Fixture results measure the proposed phrase rule only, not document safety or
generalization. Source URLs are retained as evidence metadata and never fetched.
"""

import hashlib
import json
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from urllib.parse import urlsplit

from . import store
from .detect import Finding, Page

ENGINE_VERSION = "literal-groups-v1"
SPEC_KEYS = {"title", "groups", "action", "rationale", "improvements", "tests"}
SOURCE_KEYS = {"title", "url", "evidence_status", "summary"}
SCHEMA = """
create table if not exists learning_rules (
    id integer primary key,
    spec text not null, source text not null, digest text not null,
    status text not null check(status in ('draft','tested','failed','active','retired')),
    generator text not null, created_by text not null, created_at real not null,
    results text, tested_digest text, tested_at real,
    activated_by text, activated_at real, retired_by text, retired_at real
);
create trigger if not exists learning_rule_content_immutable
before update of spec, source, digest, generator, created_by, created_at on learning_rules
begin
    select raise(abort, 'Learning rule content is immutable; create a new candidate.');
end;
create table if not exists learning_checks (
    attachment_id integer primary key, revision text not null, checked_at real not null
);
create table if not exists learning_policy (
    id integer primary key check(id=1), generation integer not null
);
insert or ignore into learning_policy(id,generation)
select 1, count(*) from learning_rules where activated_at is not null;
"""


@contextmanager
def _db():
    # Resolve store.db at call time, including its configured database path.
    con = store.db()
    try:
        con.executescript(SCHEMA)
        with con:
            yield con
    finally:
        con.close()


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _text(value, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text.")
    value = value.strip()
    if len(value) > maximum:
        raise ValueError(f"{name} must contain at most {maximum} characters.")
    if any(unicodedata.category(c) == "Cs" for c in value):
        raise ValueError(f"{name} contains unsupported characters.")
    return value


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(value.split())


def validate_spec(spec: dict) -> dict:
    """Return a bounded independent copy, or a user-readable ValueError."""
    if not isinstance(spec, dict) or set(spec) != SPEC_KEYS:
        raise ValueError("Rule fields must be title, groups, action, rationale, improvements and tests.")
    title = _text(spec["title"], "Title", 160)
    rationale = _text(spec["rationale"], "Rationale", 2000)
    action = spec["action"]
    if not isinstance(action, str) or action not in {"hold", "withheld"}:
        raise ValueError("Action must be hold or withheld.")
    groups = spec["groups"]
    if not isinstance(groups, list) or not 1 <= len(groups) <= 4:
        raise ValueError("Use between 1 and 4 phrase groups.")
    cleaned_groups = []
    for group in groups:
        if not isinstance(group, list) or not 1 <= len(group) <= 5:
            raise ValueError("Each group needs between 1 and 5 alternative phrases.")
        phrases = [_text(term, "Phrase", 80) for term in group]
        if any(not _normalize(term) for term in phrases):
            raise ValueError("Phrases must remain nonempty after normalization.")
        cleaned_groups.append(phrases)
    improvements = spec["improvements"]
    if not isinstance(improvements, list) or len(improvements) > 8:
        raise ValueError("Use at most 8 improvement proposals.")
    improvements = [_text(item, "Improvement", 500) for item in improvements]
    tests = spec["tests"]
    if not isinstance(tests, list) or not 2 <= len(tests) <= 12:
        raise ValueError("Provide between 2 and 12 fictional tests.")
    cleaned_tests = []
    for test in tests:
        if not isinstance(test, dict) or set(test) != {"name", "text", "should_match"}:
            raise ValueError("Each test needs name, text and should_match fields.")
        if type(test["should_match"]) is not bool:
            raise ValueError("Test should_match must be true or false.")
        cleaned_tests.append({"name": _text(test["name"], "Test name", 100),
                              "text": _text(test["text"], "Test text", 1500),
                              "should_match": test["should_match"]})
    if {test["should_match"] for test in cleaned_tests} != {True, False}:
        raise ValueError("Include at least one positive test and one benign control.")
    if len({test["name"] for test in cleaned_tests}) != len(cleaned_tests):
        raise ValueError("Test names must be unique.")
    return {"title": title, "groups": cleaned_groups, "action": action,
            "rationale": rationale, "improvements": improvements, "tests": cleaned_tests}


def _source(source: dict) -> dict:
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise ValueError("Source fields must be title, url, evidence_status and summary.")
    result = {key: _text(source[key], f"Source {key}", limit) for key, limit in
              (("title", 200), ("url", 2048), ("evidence_status", 80), ("summary", 6000))}
    url = result["url"]
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme in {"https", "http"} and bool(parsed.hostname)
                 and parsed.username is None and parsed.password is None)
        parsed.port  # Reject malformed ports without contacting the source.
    except ValueError:
        valid = False
    if (not valid or "\\" in url or any(c.isspace() or unicodedata.category(c)[0] == "C" for c in url)):
        raise ValueError("Source URL must be an http(s) address without credentials or whitespace.")
    return result


def _digest(spec: dict, source: dict) -> str:
    return hashlib.sha256(_json({"engine": ENGINE_VERSION, "spec": spec, "source": source}).encode()).hexdigest()


def _id(value) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("Choose a valid rule or attachment ID.")
    return value


def _record(row: sqlite3.Row) -> dict:
    record = dict(row)
    for name in ("spec", "source", "results"):
        record[name] = json.loads(record[name]) if record[name] is not None else None
    if _digest(record["spec"], record["source"]) != record["digest"]:
        raise ValueError("Rule content does not match its digest; create a new candidate.")
    return record


def _required(con, rule_id: int) -> dict:
    row = con.execute("select * from learning_rules where id=?", (_id(rule_id),)).fetchone()
    if row is None:
        raise ValueError("This rule no longer exists.")
    return _record(row)


def create_candidate(spec: dict, source: dict, actor: str, generator: str = "reviewed recipe") -> int:
    spec, source = validate_spec(spec), _source(source)
    actor, generator = _text(actor, "Actor", 200), _text(generator, "Generator", 100)
    with _db() as con:
        row = con.execute(
            "insert into learning_rules(spec,source,digest,status,generator,created_by,created_at) "
            "values (?,?,?,'draft',?,?,?)",
            (_json(spec), _json(source), _digest(spec, source), generator, actor, store.now()),
        )
        return row.lastrowid


def list_rules() -> list[dict]:
    with _db() as con:
        return [_record(row) for row in con.execute("select * from learning_rules order by id desc")]


def get_rule(rule_id: int) -> dict | None:
    with _db() as con:
        row = con.execute("select * from learning_rules where id=?", (_id(rule_id),)).fetchone()
        return _record(row) if row is not None else None


def _patterns(spec: dict) -> list[list[re.Pattern]]:
    return [[re.compile(r"(?<!\w)" + re.escape(_normalize(term)) + r"(?!\w)")
             for term in group] for group in spec["groups"]]


def _matches(patterns, normalized_text: str) -> bool:
    return all(any(pattern.search(normalized_text) for pattern in group) for group in patterns)


def _test_results(record: dict) -> dict:
    patterns = _patterns(record["spec"])
    cases = []
    for test in record["spec"]["tests"]:
        match = _matches(patterns, _normalize(test["text"]))
        cases.append({"name": test["name"], "should_match": test["should_match"],
                      "baseline_match": False, "candidate_match": match,
                      "baseline_passed": not test["should_match"],
                      "candidate_passed": match == test["should_match"]})
    passed = sum(case["candidate_passed"] for case in cases)
    total = len(cases)
    return {"rule_id": record["id"], "digest": record["digest"],
            "passed": passed == total, "passed_count": passed, "total": total,
            "baseline": {"passed": sum(case["baseline_passed"] for case in cases), "total": total},
            "candidate": {"passed": passed, "total": total}, "cases": cases}


def run_tests(rule_id: int) -> dict:
    """Compare no learned rule with this candidate on its fictional fixtures."""
    with _db() as con:
        con.execute("begin immediate")
        record = _required(con, rule_id)
        if record["status"] not in {"draft", "tested", "failed"}:
            raise ValueError("Only inactive candidates can be tested; create a new version to change a rule.")
        results = _test_results(record)
        con.execute("update learning_rules set status=?,results=?,tested_digest=?,tested_at=? where id=?",
                    ("tested" if results["passed"] else "failed", _json(results),
                     record["digest"], store.now(), rule_id))
        return results


def _expected(record: dict, expected_digest: str):
    if not isinstance(expected_digest, str) or expected_digest != record["digest"]:
        raise ValueError("The rule version changed. Reload it before continuing.")


def activate(rule_id: int, expected_digest: str, actor: str) -> dict:
    actor = _text(actor, "Actor", 200)
    with _db() as con:
        con.execute("begin immediate")
        record = _required(con, rule_id)
        _expected(record, expected_digest)
        if (record["status"] != "tested" or record["tested_digest"] != record["digest"]
                or record["results"] != _test_results(record) or not record["results"]["passed"]):
            raise ValueError("Run and pass every test for this exact candidate before activation.")
        con.execute("update learning_rules set status='active',activated_by=?,activated_at=? where id=?",
                    (actor, store.now(), rule_id))
        con.execute("update learning_policy set generation=generation+1 where id=1")
        return _required(con, rule_id)


def deactivate(rule_id: int, expected_digest: str, actor: str) -> dict:
    """Retire the rule; neither decisions nor attachment checks are changed."""
    actor = _text(actor, "Actor", 200)
    with _db() as con:
        con.execute("begin immediate")
        record = _required(con, rule_id)
        _expected(record, expected_digest)
        if record["status"] != "active":
            raise ValueError("Only an active rule can be retired.")
        con.execute("update learning_rules set status='retired',retired_by=?,retired_at=? where id=?",
                    (actor, store.now(), rule_id))
        con.execute("update learning_policy set generation=generation+1 where id=1")
        return _required(con, rule_id)


def _snapshot(con) -> tuple[list[dict], str]:
    generation = con.execute("select generation from learning_policy where id=1").fetchone()[0]
    rules = [_record(row) for row in con.execute("select * from learning_rules where status='active' order by id")]
    digest = hashlib.sha256(_json({"engine": ENGINE_VERSION, "generation": generation,
                                  "rules": [[r["id"], r["digest"]] for r in rules]}).encode()).hexdigest()
    return rules, digest


def snapshot() -> tuple[list[dict], str]:
    """Return exact rules and lifecycle revision from one read transaction."""
    with _db() as con:
        con.execute("begin")
        return _snapshot(con)


def active_rules() -> list[dict]:
    return snapshot()[0]


def revision() -> str:
    return snapshot()[1]


def apply(pages: list[Page], rules: list[dict] | None = None) -> list[Finding]:
    """Find literal groups in extracted text. OCR completeness is handled upstream."""
    rules = active_rules() if rules is None else rules
    normalized = [(page.number, _normalize(page.text)) for page in pages]
    document = " ".join(text for _, text in normalized)
    findings = []
    for record in rules:
        if record["status"] != "active":
            continue
        spec = validate_spec(record["spec"])
        if _digest(spec, record["source"]) != record["digest"]:
            raise ValueError("Rule content does not match its digest; recheck the active rules.")
        patterns = _patterns(spec)
        matches = [number for number, text in normalized if _matches(patterns, text)]
        if not matches and _matches(patterns, document):
            matches = [0]  # Required groups span pages; no single page is the evidence.
        for page in matches:
            findings.append(Finding(kind="learned_rule", label=f"L{record['id']}: {spec['title']}",
                                    evidence=f"Rule L{record['id']} matched its required phrase groups.",
                                    page=page, severity="block" if spec["action"] == "withheld" else "review",
                                    rule="learned"))
    return findings


def record_check(attachment_id: int, rev: str) -> None:
    attachment_id = _id(attachment_id)
    with _db() as con:
        con.execute("begin immediate")
        if con.execute("select 1 from attachments where id=?", (attachment_id,)).fetchone() is None:
            raise ValueError("This attachment no longer exists.")
        if not isinstance(rev, str) or rev != _snapshot(con)[1]:
            raise ValueError("Active rules changed during the check. Recheck this attachment.")
        con.execute("insert into learning_checks(attachment_id,revision,checked_at) values (?,?,?) "
                    "on conflict(attachment_id) do update set revision=excluded.revision,checked_at=excluded.checked_at",
                    (attachment_id, rev, store.now()))


def current(attachment_id: int) -> bool:
    attachment_id = _id(attachment_id)
    with _db() as con:
        con.execute("begin")
        rules, rev = _snapshot(con)
        generation = con.execute("select generation from learning_policy where id=1").fetchone()[0]
        row = con.execute("select c.revision from attachments a left join learning_checks c "
                          "on c.attachment_id=a.id where a.id=?", (attachment_id,)).fetchone()
        if row is None:
            return False
        return row["revision"] == rev if row["revision"] is not None else generation == 0 and not rules


def pending_count() -> int:
    with _db() as con:
        con.execute("begin")
        rules, rev = _snapshot(con)
        generation = con.execute("select generation from learning_policy where id=1").fetchone()[0]
        return con.execute(
            "select count(*) from attachments a left join learning_checks c on c.attachment_id=a.id "
            "where (c.revision is not null and c.revision != ?) or (c.revision is null and ?)",
            (rev, generation > 0 or bool(rules)),
        ).fetchone()[0]
