"""Public-feed leads stay separate from confirmed incidents and active rules."""

import httpx
import pytest

from gate import incident_discovery as discovery
from test_learning_flow import web

FEED = b'''<rss><channel><item><title>Fictional Argentina disclosure report</title>
<link>https://news.google.com/rss/articles/fictional-article</link>
<pubDate>Fri, 09 Oct 2026 12:00:00 GMT</pubDate><source>Fictional publisher</source></item></channel></rss>'''


def test_news_search_uses_fixed_public_endpoint_and_does_not_follow_article_links(web):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.url.host == "news.google.com" and request.url.path == "/rss/search"
        assert request.url.params["q"] == discovery.QUERY
        return httpx.Response(200, content=FEED)
    original = httpx.Client
    web.monkeypatch.setattr(discovery.httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    response = web.client.post("/learning/discover", follow_redirects=False)
    assert response.status_code == 303 and len(calls) == 1
    leads = discovery.list_leads()
    assert len(leads) == 1 and web.learning.list_rules() == []
    assert discovery.discover() == discovery.list_leads()  # newest receipt, same unique URL
    assert len(discovery.list_leads()) == 1
    page = web.client.get("/learning?lead=" + leads[0]["id"])
    assert "Unverified lead" in page.text and "cause, affected records" in page.text
    assert discovery.source_prefill(leads[0])["url"].startswith("https://news.google.com/")


def test_discovery_requires_staff_and_same_origin(web):
    assert web.anonymous.post("/learning/discover").status_code == 401
    assert web.client.post("/learning/discover", headers={"origin": "https://other.example"}).status_code == 403


@pytest.mark.parametrize("bad", [b'<!DOCTYPE rss [<!ENTITY x "content">]><rss/>', b'<broken', b'<html/>', b'x' * 256001])
def test_invalid_or_oversized_feeds_are_rejected(bad):
    with pytest.raises(ValueError):
        discovery.parse_feed(bad)


@pytest.mark.parametrize("url", [b'http://127.0.0.1/private', b'https://evil.example/report',
    b'https://news.google.com:bad/rss/articles/x', b'https://user:password@news.google.com/rss/articles/x'])
def test_unexpected_urls_are_not_saved_or_fetched(url):
    body = FEED.replace(b'https://news.google.com/rss/articles/fictional-article', url)
    assert discovery.parse_feed(body) == []
