"""Synthetic coverage and fail-closed checks. No external OCR or model calls."""

import io
import json
from types import SimpleNamespace

import pymupdf
import pytest
from PIL import Image

from gate import detect, llm
from gate.detect import Finding, Page, Scan
from gate.policy import HOLD, PUBLIC, WITHHELD, decide


SAFE_TEXT = {
    "safe_for_public": True, "personal_data": False, "health_data": False,
    "reidentification_risk": "none", "reasons": [],
}
SAFE_IMAGE = {
    "kind": "Fictional equipment drawing", "personal_data": False,
    "health_data": False, "medical_image": False, "safe_for_public": True,
}
BENIGN_TEXT = "Fictional procurement: twenty office chairs with adjustable backrests."


def make_pdf(*, image_page: int | None = None, text: str = BENIGN_TEXT, pages: int = 1) -> bytes:
    with pymupdf.open() as doc:
        for index in range(pages):
            page = doc.new_page(width=360, height=480)
            page.insert_textbox(pymupdf.Rect(20, 20, 340, 100), text, fontsize=11)
            if index == image_page:
                image = io.BytesIO()
                Image.new("RGB", (120, 80), "white").save(image, format="PNG")
                page.insert_image(pymupdf.Rect(20, 120, 300, 300), stream=image.getvalue())
        return doc.tobytes()


def clean_scan() -> Scan:
    return Scan([Page(1, BENIGN_TEXT, "text")])


def visual_scan() -> Scan:
    return Scan([Page(1, BENIGN_TEXT, "text+ocr", b"rendered", True)], ocr_used=True)


def test_long_text_does_not_hide_an_embedded_image(monkeypatch):
    calls = []

    def ocr(image, **options):
        calls.append((image.size, options))
        return "DNI: 31.846.275"  # fictional OCR output; never a real identity

    monkeypatch.setattr(detect.pytesseract, "image_to_string", ocr)
    result = detect.scan(make_pdf(image_page=0))
    assert len(result.pages[0].text) > detect.MIN_TEXT_CHARS
    assert result.pages[0].has_images and result.pages[0].image.startswith(b"\x89PNG")
    assert result.pages[0].source == "text+ocr" and result.ocr_used
    assert len(calls) == 1 and calls[0][1]["timeout"] == 20
    assert any(f.kind == "dni" and "*" in f.evidence for f in result.findings)
    assert decide(result, SAFE_TEXT, [SAFE_IMAGE])[0] == WITHHELD


def test_harmless_mixed_document_requires_both_analyses(monkeypatch):
    monkeypatch.setattr(detect.pytesseract, "image_to_string", lambda *a, **kw: BENIGN_TEXT)
    result = detect.scan(make_pdf(image_page=0))
    assert decide(result, SAFE_TEXT, [SAFE_IMAGE])[0] == PUBLIC
    assert decide(result, SAFE_TEXT, [None])[0] == HOLD
    assert decide(result, None, [SAFE_IMAGE])[0] == HOLD


def test_text_only_document_does_not_require_ocr(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("text-only page should not invoke OCR")

    monkeypatch.setattr(detect.pytesseract, "image_to_string", unexpected)
    result = detect.scan(make_pdf())
    assert not result.pages[0].has_images and not result.ocr_used
    assert not result.coverage_issues and not result.pages[0].coverage_issues
    assert decide(result, SAFE_TEXT)[0] == PUBLIC


@pytest.mark.parametrize("model", [None, {}, [], "safe", {"error": "unavailable"},
                                  {"safe_for_public": True},
                                  dict(SAFE_TEXT, reasons="safe"),
                                  dict(SAFE_TEXT, reidentification_risk="unknown")])
def test_incomplete_text_analysis_always_holds(model):
    decision, _, findings = decide(clean_scan(), model)
    assert decision == HOLD
    assert any(f["kind"] == "unchecked_text" for f in findings)


@pytest.mark.parametrize("field", ["safe_for_public", "personal_data", "health_data"])
@pytest.mark.parametrize("value", ["false", "true", 0, 1, None])
def test_text_model_flags_must_be_json_booleans(field, value):
    assert decide(clean_scan(), dict(SAFE_TEXT, **{field: value}))[0] == HOLD


@pytest.mark.parametrize("image", [None, {}, [], {"error": "unavailable"},
                                  dict(SAFE_IMAGE, safe_for_public="true"),
                                  dict(SAFE_IMAGE, personal_data="false"),
                                  dict(SAFE_IMAGE, health_data=0),
                                  dict(SAFE_IMAGE, medical_image=0),
                                  dict(SAFE_IMAGE, kind="")])
def test_missing_or_malformed_image_analysis_holds(image):
    decision, _, findings = decide(visual_scan(), SAFE_TEXT, [image])
    assert decision == HOLD
    assert any(f["kind"] == "unchecked_image" for f in findings)


def test_vision_finding_preserves_actual_page_number(monkeypatch):
    monkeypatch.setattr(detect.pytesseract, "image_to_string", lambda *a, **kw: BENIGN_TEXT)
    result = detect.scan(make_pdf(image_page=1, pages=2))
    decision, _, findings = decide(result, SAFE_TEXT, [None, dict(SAFE_IMAGE, medical_image=True)])
    assert decision == HOLD
    assert [f["page"] for f in findings if f["kind"] == "model_image"] == [2]
    assert decide(result, SAFE_TEXT, [SAFE_IMAGE])[0] == HOLD  # truncated/misaligned results


def test_ocr_error_is_coverage_failure_not_an_exception(monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("synthetic-sensitive-value must not become a finding")

    monkeypatch.setattr(detect.pytesseract, "image_to_string", unavailable)
    result = detect.scan(make_pdf(image_page=0))
    assert result.pages[0].coverage_issues == ["ocr_failed"]
    assert result.pages[0].image
    decision, _, findings = decide(result, SAFE_TEXT, [SAFE_IMAGE])
    assert decision == HOLD
    assert "synthetic-sensitive-value" not in json.dumps(findings)


def test_render_failure_still_requires_review(monkeypatch):
    monkeypatch.setattr(detect, "MAX_RENDER_PIXELS", 1)
    result = detect.scan(make_pdf(image_page=0))
    assert result.pages[0].coverage_issues == ["page_render_limit"]
    assert decide(result, SAFE_TEXT, [SAFE_IMAGE])[0] == HOLD


def test_invalid_pdf_and_empty_scan_are_not_public():
    result = detect.scan(b"This is not a PDF")
    assert result.coverage_issues == ["pdf_extraction_failed"]
    assert decide(result, SAFE_TEXT)[0] == HOLD
    assert decide(Scan([]), SAFE_TEXT)[0] == HOLD


def test_deterministic_block_has_precedence_over_missing_analysis():
    result = visual_scan()
    result.findings = [Finding("dni", "Fictional ID", "31.***.275", 1, "block", "personal_id")]
    result.coverage_issues = ["ocr_failed"]
    assert decide(result, None, [None])[0] == WITHHELD


def fake_model(monkeypatch, raw):
    monkeypatch.setenv("AKASHML_API_KEY", "synthetic-test-key")
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=raw))],
                               model="synthetic-test-model")
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response)))
    monkeypatch.setattr(llm, "OpenAI", lambda **kw: client)


@pytest.mark.parametrize("raw", ["{}", "[]", "null", "not JSON", '{"safe_for_public":"true"}'])
def test_provider_malformed_responses_do_not_escape_as_safe(monkeypatch, raw):
    fake_model(monkeypatch, raw)
    assert "error" in llm.review(BENIGN_TEXT)
    assert "error" in llm.review_image(b"synthetic-image")


def test_valid_provider_contract_is_preserved(monkeypatch):
    fake_model(monkeypatch, json.dumps(SAFE_TEXT))
    assert llm.review(BENIGN_TEXT) == dict(SAFE_TEXT, model="synthetic-test-model")
    fake_model(monkeypatch, json.dumps(SAFE_IMAGE))
    assert llm.review_image(b"synthetic-image") == dict(SAFE_IMAGE, model="synthetic-test-model")


def test_missing_key_does_not_call_provider(monkeypatch):
    monkeypatch.setenv("AKASHML_API_KEY", "")
    monkeypatch.setattr(llm, "OpenAI", lambda **kw: pytest.fail("unexpected provider call"))
    assert llm.review(BENIGN_TEXT) is None
    assert llm.review_image(b"synthetic-image") is None


def test_long_text_is_held_instead_of_silently_truncated(monkeypatch):
    monkeypatch.setenv("AKASHML_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(llm, "OpenAI", lambda **kw: pytest.fail("partial analysis must not be sent"))
    model = llm.review("a" * (llm.MAX_TEXT_CHARS + 1))
    assert model == {"error": "text_analysis_incomplete"}
    assert decide(clean_scan(), model)[0] == HOLD


def test_long_document_includes_final_page_in_model_request_and_decision(monkeypatch):
    monkeypatch.setenv("AKASHML_API_KEY", "synthetic-test-key")
    tail = "Final page: fictional private patient details require review."
    text = (BENIGN_TEXT + "\n") * 1800 + tail
    assert 12000 < len(text) < llm.MAX_TEXT_CHARS
    calls = []
    result = dict(SAFE_TEXT, safe_for_public=False, personal_data=True,
                  reidentification_risk="high", reasons=["Fictional final-page personal data"])

    def respond(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(result)))],
                               model="synthetic-long-context-model")

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=respond)))
    monkeypatch.setattr(llm, "OpenAI", lambda **kwargs: client)
    reviewed = llm.review(text)
    assert len(calls) == 1
    assert calls[0]["messages"][1]["content"] == llm.PROMPT + text
    assert calls[0]["messages"][1]["content"].endswith(tail)
    assert decide(Scan([Page(1, text, "text")]), reviewed)[0] == HOLD


def test_client_setup_errors_are_sanitized_and_held(monkeypatch):
    monkeypatch.setenv("AKASHML_API_KEY", "synthetic-test-key")

    def broken_client(**kwargs):
        raise ValueError("synthetic-sensitive-value")

    monkeypatch.setattr(llm, "OpenAI", broken_client)
    text_result, image_result = llm.review(BENIGN_TEXT), llm.review_image(b"synthetic-image")
    assert text_result == {"error": "text_analysis_unavailable"}
    assert image_result == {"error": "image_analysis_unavailable"}
    assert decide(visual_scan(), text_result, [image_result])[0] == HOLD
