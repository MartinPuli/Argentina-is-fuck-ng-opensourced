"""Discover public reporting through a fixed Google News RSS query.

Headlines are leads, not confirmed leaks or forensic evidence. No article bodies,
leaked records or headline URLs are fetched. Discovery never creates/activates rules.
"""

import hashlib
import time
from defusedxml import ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx

from . import store

QUERY = 'Argentina ("filtración de datos" OR "datos filtrados" OR "ciberataque") when:30d'
ENDPOINT = "https://news.google.com/rss/search"
SCHEMA = """
create table if not exists incident_leads (
    id text primary key, title text not null, url text not null, publisher text not null,
    published_at text not null, discovered_at real not null
);
"""


def _db():
    con = store.db()
    con.executescript(SCHEMA)
    return con


def list_leads() -> list[dict]:
    with _db() as con:
        return [dict(row) for row in con.execute(
            "select * from incident_leads order by discovered_at desc,published_at desc limit 12")]


def get_lead(lead_id: str) -> dict | None:
    with _db() as con:
        row = con.execute("select * from incident_leads where id=?", (lead_id,)).fetchone()
    return dict(row) if row else None


def parse_feed(body: bytes) -> list[dict]:
    if len(body) > 256_000 or b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
        raise ValueError("News feed exceeds the supported format or size.")
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        raise ValueError("News feed could not be read.") from None
    if root.tag != "rss":
        raise ValueError("Expected a public RSS news feed.")
    leads = {}
    for item in root.findall("./channel/item")[:50]:
        title = " ".join((item.findtext("title") or "").split())[:160]
        url = (item.findtext("link") or "").strip()
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError:
            continue
        if (not title or parsed.scheme != "https" or parsed.hostname != "news.google.com"
                or parsed.username or parsed.password or port not in (None, 443)
                or not parsed.path.startswith("/rss/articles/") or len(url) > 1000):
            continue
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "").isoformat()
        except (ValueError, TypeError, OverflowError):
            continue
        identity = hashlib.sha256(url.encode()).hexdigest()
        leads[identity] = {"id": identity, "title": title, "url": url,
            "publisher": " ".join((item.findtext("source") or "Unknown publisher").split())[:160],
            "published_at": published, "discovered_at": time.time()}
    return list(leads.values())[:12]


def discover() -> list[dict]:
    try:
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
            with client.stream("GET", ENDPOINT, params={"q": QUERY, "hl": "es-419", "gl": "AR", "ceid": "AR:es-419"}) as response:
                if response.status_code != 200:
                    raise ValueError("Public news search is unavailable. Existing leads were preserved.")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 256_000:
                        raise ValueError("News feed exceeds the supported size.")
        leads = parse_feed(bytes(body))
    except httpx.HTTPError:
        raise ValueError("Public news search is unavailable. Existing leads were preserved.") from None
    with _db() as con:
        for lead in leads:
            con.execute("insert or replace into incident_leads values (?,?,?,?,?,?)",
                        tuple(lead[key] for key in ("id", "title", "url", "publisher", "published_at", "discovered_at")))
    return leads


def source_prefill(lead: dict) -> dict:
    return {"title": lead["title"], "url": lead["url"], "summary": (
        f"Google News indexed a report from {lead['publisher']} dated {lead['published_at']}. "
        f"Headline: {lead['title']}. This is an unverified discovery lead, not a confirmed incident. "
        "The article body was not retrieved; the cause, affected records and relevance to PDF publication are unknown. "
        "Add reviewed, sanitized evidence before proposing a rule.")}
