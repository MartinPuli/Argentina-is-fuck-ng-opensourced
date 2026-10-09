"""Synthetic rule fixtures, lifecycle checks and revision-based access checks."""

import copy
import sqlite3

import pytest

from gate import learning, store
from gate.detect import Page


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "learning.db")


@pytest.fixture
def spec():
    return {
        "title": "Clinical record with an affiliate reference",
        "groups": [["historia clínica", "medical record"], ["afiliado", "affiliate"]],
        "action": "withheld",
        "rationale": "A fictional example links medical context to a beneficiary reference.",
        "improvements": ["Keep benefit records in the private document workflow."],
        "tests": [
            {"name": "fictional beneficiary", "text": "HISTORIA CLÍNICA: afiliado SYNTH-001", "should_match": True},
            {"name": "public specification", "text": "Specification for clinical office chairs.", "should_match": False},
        ],
    }


@pytest.fixture
def source():
    return {"title": "Synthetic public incident summary", "url": "https://example.org/incident",
            "evidence_status": "fictional test", "summary": "Synthetic case metadata; no source is fetched."}


def candidate(spec, source):
    return learning.create_candidate(spec, source, "reviewer")


def enabled(spec, source):
    rule_id = candidate(spec, source)
    result = learning.run_tests(rule_id)
    assert result["passed"]
    return learning.activate(rule_id, learning.get_rule(rule_id)["digest"], "reviewer")


def attachment(decision="public"):
    with store.db() as con:
        return con.execute("insert into attachments(filename,decision,pdf) values (?,?,?)",
                           ("fictional.pdf", decision, b"synthetic")).lastrowid


def page(text, number=1):
    return Page(number, text, "text")


def test_candidate_is_an_independent_immutable_copy(spec, source):
    rule_id = candidate(spec, source)
    initial = learning.get_rule(rule_id)
    spec["groups"][0][0] = "changed"
    source["summary"] = "changed"
    saved = learning.get_rule(rule_id)
    assert saved == initial
    assert saved["status"] == "draft" and saved["results"] is None
    assert saved["created_by"] == "reviewer" and saved["generator"] == "reviewed recipe"
    with store.db() as con, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        con.execute("update learning_rules set spec=? where id=?", ("{}", rule_id))


def test_report_measures_candidate_against_no_learned_rule(spec, source):
    rule_id = candidate(spec, source)
    result = learning.run_tests(rule_id)
    assert result["passed"] is True
    assert result["baseline"] == {"passed": 1, "total": 2}
    assert result["candidate"] == {"passed": 2, "total": 2}
    assert result["passed_count"] == result["total"] == 2
    assert [case["candidate_match"] for case in result["cases"]] == [True, False]
    assert all(case["baseline_match"] is False for case in result["cases"])
    assert "SYNTH-001" not in str(result)
    assert learning.get_rule(rule_id)["tested_digest"] == result["digest"]
    assert learning.get_rule(rule_id)["status"] == "tested"


def test_normalization_boundaries_and_benign_controls(spec, source):
    enabled(spec, source)
    texts = ["HISTO\u0301RIA\n\tCLI\u0301NICA : AFILIADO SYNTH-003",
             "medical RECORD for affiliate SYNTH-004"]
    for text in texts:
        assert len(learning.apply([page(text)])) == 1
    for text in ["historia clinica", "afiliado only", "prehistoria clinica afiliado",
                 "historia clinica afiliados", "ordinary public chair specification"]:
        assert learning.apply([page(text)]) == []


def test_regex_characters_are_literal_not_executable(spec, source):
    spec["groups"] = [["a.*b"]]
    spec["tests"] = [
        {"name": "literal", "text": "literal a.*b marker", "should_match": True},
        {"name": "regex-like benign", "text": "axxxb marker", "should_match": False},
    ]
    enabled(spec, source)
    assert learning.apply([page("literal a.*b marker")])
    assert not learning.apply([page("axxxb marker")])


@pytest.mark.parametrize("field,value", [
    ("title", 42), ("title", "x" * 161), ("rationale", ""), ("action", "public"),
    ("action", ["withheld"]), ("groups", []), ("groups", [["x"]] * 5),
    ("groups", [["x"] * 6]), ("groups", [["x" * 81]]), ("groups", [[7]]),
    ("groups", [["\u0301"]]), ("improvements", "not a list"),
    ("improvements", ["x"] * 9), ("improvements", ["x" * 501]),
    ("tests", []), ("tests", "not tests"),
])
def test_schema_rejects_invalid_types_and_limits(spec, field, value):
    spec[field] = value
    with pytest.raises(ValueError):
        learning.validate_spec(spec)


@pytest.mark.parametrize("mutation", ["unknown", "missing", "bool", "no_positive", "no_negative", "oversized", "many", "duplicate"])
def test_test_schema_requires_a_bounded_positive_and_control(spec, mutation):
    if mutation == "unknown":
        spec["python"] = "raise RuntimeError('must never run')"
    elif mutation == "missing":
        del spec["tests"][0]["name"]
    elif mutation == "bool":
        spec["tests"][0]["should_match"] = 1
    elif mutation == "no_positive":
        spec["tests"][0]["should_match"] = False
    elif mutation == "no_negative":
        spec["tests"][1]["should_match"] = True
    elif mutation == "oversized":
        spec["tests"][0]["text"] = "x" * 1501
    elif mutation == "many":
        spec["tests"] *= 7
    elif mutation == "duplicate":
        spec["tests"][1]["name"] = spec["tests"][0]["name"]
    with pytest.raises(ValueError):
        learning.validate_spec(spec)


@pytest.mark.parametrize("url", ["file:///tmp/private", "javascript:alert(1)", "https://user:password@example.org/x",
                                 "https://user@example.org", "https:///missing-host", "https://example.org:invalid/x",
                                 "https://example.org/a b", "https://exam\nple.org", "https://example.org\\x"])
def test_source_url_is_metadata_without_credentials(spec, source, url):
    source["url"] = url
    with pytest.raises(ValueError, match="Source URL"):
        candidate(spec, source)
    assert learning.list_rules() == []


def test_source_summary_accepts_bounded_proposer_context(spec, source):
    source["summary"] = "x" * 6000
    rule_id = candidate(spec, source)
    assert len(learning.get_rule(rule_id)["source"]["summary"]) == 6000
    source["summary"] += "x"
    with pytest.raises(ValueError, match="6000"):
        candidate(spec, source)


def test_activation_requires_test_and_exact_digest(spec, source):
    rule_id = candidate(spec, source)
    digest = learning.get_rule(rule_id)["digest"]
    with pytest.raises(ValueError, match="Run and pass"):
        learning.activate(rule_id, digest, "reviewer")
    learning.run_tests(rule_id)
    with pytest.raises(ValueError, match="version changed"):
        learning.activate(rule_id, "0" * 64, "reviewer")
    record = learning.activate(rule_id, digest, "reviewer")
    assert record["status"] == "active" and record["activated_by"] == "reviewer"
    with pytest.raises(ValueError):
        learning.activate(rule_id, digest, "reviewer")
    with pytest.raises(ValueError):
        learning.run_tests(rule_id)


def test_failed_benign_control_blocks_activation(spec, source):
    spec["tests"][1]["text"] = "historia clinica afiliado benign example"
    rule_id = candidate(spec, source)
    result = learning.run_tests(rule_id)
    assert result["passed"] is False and result["passed_count"] == 1
    assert learning.get_rule(rule_id)["status"] == "failed"
    with pytest.raises(ValueError, match="Run and pass"):
        learning.activate(rule_id, result["digest"], "reviewer")


def test_stored_result_cannot_override_actual_fixture_outcomes(spec, source):
    rule_id = candidate(spec, source)
    result = learning.run_tests(rule_id)
    with store.db() as con:
        con.execute("update learning_rules set results=? where id=?", ('{"passed":true}', rule_id))
    with pytest.raises(ValueError, match="Run and pass"):
        learning.activate(rule_id, result["digest"], "reviewer")


@pytest.mark.parametrize("action,severity", [("withheld", "block"), ("hold", "review")])
def test_only_active_rules_apply_and_evidence_omits_private_text(spec, source, action, severity):
    spec["action"] = action
    rule_id = candidate(spec, source)
    pages = [page("historia clínica afiliado SYNTH-PRIVATE-019")]
    assert learning.apply(pages) == []
    learning.run_tests(rule_id)
    record = learning.activate(rule_id, learning.get_rule(rule_id)["digest"], "reviewer")
    findings = learning.apply(pages)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule == "learned" and finding.kind == "learned_rule"
    assert finding.severity == severity and finding.page == 1
    assert f"L{rule_id}" in finding.label and spec["title"] in finding.label
    assert "SYNTH-PRIVATE" not in finding.evidence
    assert "historia" not in finding.evidence
    with pytest.raises(ValueError, match="version changed"):
        learning.deactivate(rule_id, "bad-digest", "reviewer")
    retired = learning.deactivate(rule_id, record["digest"], "reviewer")
    assert retired["retired_by"] == "reviewer" and retired["status"] == "retired"
    assert learning.apply(pages) == []
    with pytest.raises(ValueError):
        learning.activate(rule_id, record["digest"], "reviewer")


def test_cross_page_groups_have_a_document_level_finding(spec, source):
    enabled(spec, source)
    findings = learning.apply([page("historia clinica", 1), page("afiliado SYNTH-002", 2)])
    assert len(findings) == 1 and findings[0].page == 0
    findings = learning.apply([page("historia clinica afiliado SYNTH-002", 1), page("afiliado", 2)])
    assert [finding.page for finding in findings] == [1]


def test_snapshot_remains_consistent_for_a_scan_but_cannot_mark_stale_result_current(spec, source):
    attachment_id = attachment()
    record = enabled(spec, source)
    rules, rev = learning.snapshot()
    assert rev == learning.revision() and rules == learning.active_rules()
    second_spec = copy.deepcopy(spec)
    second_spec["title"] = "A second lesson"
    enabled(second_spec, source)
    assert learning.revision() != rev
    assert len(learning.apply([page("historia clinica afiliado")], rules=rules)) == 1
    assert len(learning.apply([page("historia clinica afiliado")])) == 2
    with pytest.raises(ValueError, match="changed during"):
        learning.record_check(attachment_id, rev)
    assert not learning.current(attachment_id)
    assert record["id"] == rules[0]["id"]


def test_revision_invalidation_retirement_and_legacy_rows(spec, source):
    tracked, legacy = attachment(), attachment()
    empty_revision = learning.revision()
    assert learning.current(tracked) and learning.current(legacy)
    assert learning.pending_count() == 0
    record = enabled(spec, source)
    active_revision = learning.revision()
    assert active_revision != empty_revision
    assert learning.pending_count() == 2 and not learning.current(tracked)
    learning.record_check(tracked, active_revision)
    assert learning.current(tracked) and not learning.current(legacy)
    assert learning.pending_count() == 1
    learning.deactivate(record["id"], record["digest"], "reviewer")
    assert learning.revision() not in {empty_revision, active_revision}
    assert not learning.current(tracked)  # Retirement does not bless a tracked stale check.
    assert not learning.current(legacy)  # Legacy exemption ends after the first activation.
    assert learning.pending_count() == 2
    with store.db() as con:
        assert [r[0] for r in con.execute("select decision from attachments")] == ["public", "public"]
    learning.record_check(tracked, learning.revision())
    assert learning.current(tracked) and learning.pending_count() == 1
    learning.record_check(legacy, learning.revision())
    assert learning.current(legacy) and learning.pending_count() == 0


def test_retirement_does_not_reuse_the_original_empty_revision(spec, source):
    attachment_id = attachment()
    original = learning.revision()
    learning.record_check(attachment_id, original)
    record = enabled(spec, source)
    assert not learning.current(attachment_id)
    learning.deactivate(record["id"], record["digest"], "reviewer")
    assert learning.revision() != original
    assert learning.active_rules() == []
    assert not learning.current(attachment_id) and learning.pending_count() == 1
    with pytest.raises(ValueError, match="changed during"):
        learning.record_check(attachment_id, original)
    learning.record_check(attachment_id, learning.revision())
    assert learning.current(attachment_id) and learning.pending_count() == 0


def test_policy_metadata_initialization_preserves_existing_activation_history(spec, source):
    attachment_id = attachment()
    record = enabled(spec, source)
    learning.deactivate(record["id"], record["digest"], "reviewer")
    # Simulate upgrading the early prototype, which had rules but no generation table.
    with store.db() as con:
        con.execute("drop table learning_policy")
    assert not learning.current(attachment_id)
    assert learning.pending_count() == 1


def test_revision_is_unaffected_by_drafts_or_test_results(spec, source):
    rev = learning.revision()
    rule_id = candidate(spec, source)
    assert learning.revision() == rev
    learning.run_tests(rule_id)
    assert learning.revision() == rev


def test_ids_missing_attachments_and_actor_validation(spec, source):
    assert learning.get_rule(999) is None and not learning.current(999)
    with pytest.raises(ValueError, match="no longer exists"):
        learning.run_tests(999)
    with pytest.raises(ValueError, match="no longer exists"):
        learning.record_check(999, learning.revision())
    for invalid in (True, "1", 0, -1, 1.1):
        with pytest.raises(ValueError):
            learning.get_rule(invalid)
    with pytest.raises(ValueError, match="Actor"):
        learning.create_candidate(spec, source, " ")


def test_database_path_is_resolved_at_runtime(spec, source, tmp_path, monkeypatch):
    candidate(spec, source)
    first_path = store.DB_PATH
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "different.db")
    assert learning.list_rules() == []
    monkeypatch.setattr(store, "DB_PATH", first_path)
    assert len(learning.list_rules()) == 1
