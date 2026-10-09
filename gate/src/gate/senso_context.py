"""Senso REST integration: public guideline pack in, scoped cited passages out.

No PDF bytes, personal records or credentials are uploaded. Remote passages are
untrusted evidence; neither retrieval nor ingestion can activate a rule.
"""

import hashlib
import json
import os
import time
import unicodedata
from uuid import UUID
from urllib.parse import quote

import httpx

from . import store
from .rules import guideline_pack

API = "https://apiv2.senso.ai/api/v1"
MAX_RESPONSE = 256_000
SCHEMA = """
create table if not exists senso_documents (
    credential_hash text not null, digest text not null, content_id text not null,
    node_id text not null, org_id text not null, state text not null,
    checked_at real not null, primary key (credential_hash,digest)
);
create table if not exists learning_rule_context (
    rule_id integer primary key, snapshot text not null
);
create trigger if not exists learning_context_immutable
before update on learning_rule_context begin
    select raise(abort, 'Proposal context is immutable; create a new candidate.');
end;
"""


class SensoRequestError(ValueError):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def _db():
    con = store.db()
    con.executescript(SCHEMA)
    return con


def configured() -> bool:
    return bool(os.getenv("SENSO_API_KEY", "").strip())


def _credential_hash() -> str:
    return hashlib.sha256(os.getenv("SENSO_API_KEY", "").encode()).hexdigest()


def _uuid(value) -> str:
    if not isinstance(value, str):
        raise ValueError("Senso returned an invalid reference.")
    try:
        return str(UUID(value))
    except ValueError:
        raise ValueError("Senso returned an invalid reference.") from None


def _clean(value, maximum: int) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join("".join(c for c in value if not unicodedata.category(c).startswith("C")).split())[:maximum]


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    if not configured():
        raise ValueError("Senso is not configured. Set SENSO_API_KEY on the server.")
    headers = {"X-API-Key": os.environ["SENSO_API_KEY"].strip(), "X-Senso-Signals": "off"}
    try:
        with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
            with client.stream(method, API + path, headers=headers, json=payload) as response:
                if response.status_code not in (200, 202):
                    messages = {401: "Senso rejected the credential.", 402: "Senso credits are required.",
                                403: "Senso denied access to this operation.", 404: "Senso source is unavailable.",
                                409: "Senso already has this content; reconcile the existing source before retrying.",
                                429: "Senso rate limit reached. Try again later."}
                    raise SensoRequestError(messages.get(response.status_code, "Senso request failed. No rule was created."), response.status_code)
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE:
                        raise ValueError("Senso response exceeded the allowed size.")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("Senso returned an invalid response.")
        return data
    except (httpx.HTTPError, json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Senso is unavailable or returned an unreadable response. No rule was created.") from None


def status() -> dict:
    """Local receipt, not a network probe. A key alone never means connected."""
    pack = guideline_pack()
    with _db() as con:
        row = con.execute("select * from senso_documents where credential_hash=? and digest=?",
                          (_credential_hash(), pack["digest"])).fetchone() if configured() else None
    return {"configured": configured(), "state": row["state"] if row else "not_synced" if configured() else "not_configured",
            "ready": bool(row and row["state"] == "complete"), "digest": pack["digest"],
            "content_id": row["content_id"] if row else None, "checked_at": row["checked_at"] if row else None,
            "detail": "Local ingestion receipt; a successful proposal retrieval verifies current access."}


def sync() -> dict:
    current = status()
    if current["content_id"]:
        return refresh()
    pack = guideline_pack()
    org_id = _uuid(_request("GET", "/org/me").get("org_id"))
    payload = {"title": "Publication Gate guidelines " + pack["digest"][:12], "text": pack["text"]}
    folder = os.getenv("SENSO_FOLDER_ID", "").strip()
    if folder:
        payload["kb_folder_node_id"] = _uuid(folder)
    try:
        data = _request("POST", "/org/kb/raw", payload)
    except SensoRequestError as exc:
        if exc.status_code != 409:
            raise
        # A new server or a lost response may have no local receipt for an existing
        # source. Reuse only an exact body in this organization, never title alone.
        found = _request("GET", "/org/kb/find?q=" + quote(payload["title"], safe="") + "&limit=10")
        nodes = found.get("nodes")
        data = None
        for node in (nodes if isinstance(nodes, list) else [])[:10]:
            if not isinstance(node, dict) or node.get("type") != "content" or node.get("org_id") != org_id:
                continue
            node_id = _uuid(node.get("kb_node_id"))
            detail = _request("GET", "/org/kb/nodes/" + node_id + "/content")
            if detail.get("text") == pack["text"] and detail.get("org_id") == org_id:
                data = {**detail, "kb_node_id": node_id}
                break
        if data is None:
            raise ValueError("Senso has duplicate content, but no accessible exact guideline pack was found.") from None
    content_id, node_id = _uuid(data.get("id")), _uuid(data.get("kb_node_id"))
    if _uuid(data.get("org_id")) != org_id:
        raise ValueError("Senso returned a source from a different organization.")
    state = data.get("processing_status", "processing")
    if state not in {"pending", "processing", "complete", "failed"}:
        raise ValueError("Senso returned an unknown ingestion state.")
    with _db() as con:
        con.execute("insert or replace into senso_documents values (?,?,?,?,?,?,?)",
                    (_credential_hash(), pack["digest"], content_id, node_id, org_id, state, time.time()))
    return status()


def refresh() -> dict:
    with _db() as con:
        row = con.execute("select * from senso_documents where credential_hash=? and digest=?",
                          (_credential_hash(), guideline_pack()["digest"])).fetchone()
    if not row:
        raise ValueError("Sync the current guideline pack to Senso first.")
    data = _request("GET", "/org/kb/nodes/" + _uuid(row["node_id"]))
    content = data.get("content")
    if not isinstance(content, dict) or _uuid(content.get("id")) != row["content_id"]:
        raise ValueError("Senso source does not match the synced guideline pack.")
    state = content.get("processing_status")
    if state not in {"pending", "processing", "complete", "failed"}:
        raise ValueError("Senso returned an unknown ingestion state.")
    if state == "complete":
        detail = _request("GET", "/org/kb/nodes/" + _uuid(row["node_id"]) + "/content")
        if (detail.get("id") != row["content_id"] or detail.get("org_id") != row["org_id"]
                or detail.get("text") != guideline_pack()["text"]):
            raise ValueError("The remote guideline pack changed. It cannot be used as approved context.")
    with _db() as con:
        con.execute("update senso_documents set state=?,checked_at=? where credential_hash=? and digest=?",
                    (state, time.time(), _credential_hash(), row["digest"]))
    return status()


def retrieve(topic: str) -> dict:
    receipt = refresh()
    if not receipt["ready"]:
        raise ValueError("The Senso guideline pack is not ready. Refresh after processing completes.")
    topic = _clean(topic, 160)
    data = _request("POST", "/org/search/context", {
        "query": "Publication restrictions, lawful disclosure and reidentification safeguards for: " + topic,
        "max_results": 5, "content_ids": [receipt["content_id"]], "require_scoped_ids": True,
    })
    results = data.get("results")
    if not isinstance(results, list):
        raise ValueError("Senso returned an invalid context response.")
    with _db() as con:
        approved = con.execute("select node_id from senso_documents where credential_hash=? and digest=?",
                               (_credential_hash(), receipt["digest"])).fetchone()
    passages = []
    for result in results[:5]:
        if not isinstance(result, dict) or result.get("content_id") != receipt["content_id"]:
            raise ValueError("Senso returned context outside the approved guideline scope.")
        text = _clean(result.get("chunk_text"), 4000)
        version = _uuid(result.get("version_id"))
        node_id = _uuid(result.get("kb_node_id"))
        if not text:
            continue
        if node_id != approved[0] or text not in _clean(guideline_pack()["text"], 100_000):
            raise ValueError("Senso returned a passage that does not match the approved guideline pack.")
        passages.append({"text": text, "content_id": receipt["content_id"], "version_id": version,
                         "node_id": node_id, "title": _clean(result.get("title"), 200)})
    if not passages:
        raise ValueError("Senso found no guideline context. No Senso-backed rule was created.")
    return {"provider": "Senso", "guideline_digest": receipt["digest"], "retrieved_at": time.time(),
            "official_sources": guideline_pack()["sources"],
            "passages": passages, "authority": "Untrusted retrieved context; local reviewed policy and official sources prevail."}


def save_context(con, rule_id: int, context: dict) -> None:
    """Called in the candidate's transaction, never from a user-supplied JSON body."""
    con.execute("insert into learning_rule_context values (?,?)",
                (rule_id, json.dumps(context, sort_keys=True, ensure_ascii=False)))


def rule_context(rule_id: int) -> dict | None:
    with _db() as con:
        row = con.execute("select snapshot from learning_rule_context where rule_id=?", (rule_id,)).fetchone()
    return json.loads(row[0]) if row else None
