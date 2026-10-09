# Cloudflare / Accenture — UK protective DNS

**Snapshot:** October 9, 2026 · **Depth:** targeted capability scan
**Primary source:** [Official page](https://www.ncsc.gov.uk/information/pdns)

## Verified source statement

Government-confirmed deployment. The UK NCSC identifies these companies as the implementers of its protective DNS service. It refuses to resolve known malicious domains and provides operational logs. The page was reviewed September 17, 2024 and remains available at this research cutoff.

## Boundary and evidence strength

Network-level prevention. DNS is the address lookup that commonly precedes a connection. This service is a useful enforcement layer, not evidence that every database query or export is safe.

## Implication for BREACHSTOP

Reuse an institution's existing destination filtering. Our proposed record-access checks and repair tests serve a different purpose. A favorable DNS result must never authorize a sensitive export.

## Coverage limits

Pricing, commercial licensing terms, SEO metrics, reviews and market share were not collected. Firecrawl and DataForSEO tools were unavailable; official pages were retrieved with the browsing tool. This is a technical comparison, not a purchasing recommendation or a full competitive audit.

## Raw data sources

Local, gitignored cache: `raw/research/2026-10-09/scrapes/`. It contains the retrieval responses used for this comparison. Third-party text is not redistributed with this repository; the primary URLs above remain the public audit trail.
