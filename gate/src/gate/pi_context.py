"""Pi Security context adapter boundary. NOT CONNECTED.

Milestone 1 of docs/research/PI-IMPLEMENTATION-PLAN.md asks for a narrow,
read-only `PiContextProvider`. This module defines that contract and the
normalization every future adapter must pass through. It ships no network
client: Pi's hosted MCP server (https://mcp.pi.security/mcp) accepts only
OAuth sessions for a Pi tenant, and this project has no tenant. The only
provider here reports `not_connected`, so nothing in the gate can present a
result as coming from Pi.

Rules carried over from the plan:
- Remote text is untrusted evidence, never instructions. It is bounded and
  stripped of control characters before any caller sees it.
- Tenant and repository identifiers are supplied explicitly, never inferred.
- A missing match is a coverage gap, not permission to invent policy.
- Pi context can never publish a PDF or activate a rule. Callers attribute a
  candidate to Pi only when a provider reference exists (see `generator_label`).
"""

import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Protocol

PI_MCP_URL = "https://mcp.pi.security/mcp"
DOCS = {
    "product": "https://www.pi.security/",
    "connector": "https://github.com/pi-sloane/claude-plugin",
    "setup": "https://github.com/pi-sloane/claude-plugin/blob/main/SETUP.md",
    "plan": "docs/research/PI-IMPLEMENTATION-PLAN.md",
}
STATUSES = ("ok", "coverage_gap", "not_connected", "unavailable")
MAX_TASK = 500
MAX_ITEMS = 8
MAX_ITEM = 1000
MAX_REFERENCE = 200
REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
NOT_CONNECTED = ("Pi is not connected. Pi's hosted connector requires a Pi Security account with "
                 "tenant access and an OAuth sign-in; this deployment has neither.")


class PiNotConnected(RuntimeError):
    pass


@dataclass(frozen=True)
class PiIdentity:
    subject: str
    tenant: str
    scopes: tuple[str, ...]


@dataclass(frozen=True)
class PiContext:
    status: str
    detail: str
    provider_reference: str | None = None
    guidance: tuple[str, ...] = field(default_factory=tuple)
    references: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"status": self.status, "detail": self.detail,
                "provider_reference": self.provider_reference,
                "guidance": list(self.guidance), "references": list(self.references)}


class PiContextProvider(Protocol):
    """Read-only contract. Write operations (report upload, design review) are out of scope."""

    name: str

    def whoami(self) -> PiIdentity: ...

    def task_context(self, task: str, repository: str) -> PiContext: ...

    def finding_context(self, finding_id: str) -> PiContext: ...


def _clean(value, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    value = "".join(" " if unicodedata.category(c)[0] in "CZ" and c != " " else c
                    for c in unicodedata.normalize("NFC", value))
    value = " ".join(value.split())
    return value[:limit]


def validate_task(task: str, repository: str) -> tuple[str, str]:
    """Require a concrete task and an explicitly supplied owner/name repository identifier."""
    task = _clean(task, MAX_TASK + 1)
    if not task or len(task) > MAX_TASK:
        raise ValueError(f"Describe the task in 1-{MAX_TASK} characters.")
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        raise ValueError("Supply the repository identifier explicitly as owner/name.")
    return task, repository


def normalize_context(raw) -> PiContext:
    """Turn an adapter's raw response into a bounded PiContext.

    A response without a provider reference cannot be `ok`; an empty guidance list
    is a coverage gap. Unknown shapes become `unavailable`.
    """
    if not isinstance(raw, dict):
        return PiContext("unavailable", "Pi returned an unreadable response.")
    reference = _clean(raw.get("id") or raw.get("reference"), MAX_REFERENCE) or None
    items = raw.get("guidance")
    guidance = tuple(text for text in (_clean(item, MAX_ITEM) for item in
                                       (items if isinstance(items, list) else [])[:MAX_ITEMS]) if text)
    refs = raw.get("references")
    references = tuple(text for text in (_clean(item, MAX_ITEM) for item in
                                         (refs if isinstance(refs, list) else [])[:MAX_ITEMS]) if text)
    if reference is None:
        return PiContext("unavailable", "Pi response had no reference identifier; it is not counted.")
    if not guidance:
        return PiContext("coverage_gap", "Pi returned no matching guidance for this task.", reference,
                         references=references)
    return PiContext("ok", "Untrusted Pi guidance; verify before use.", reference, guidance, references)


def generator_label(base: str, context: PiContext | None) -> str:
    """Attribute a candidate to Pi only when real, referenced context was used."""
    if context is not None and context.status == "ok" and context.provider_reference:
        return f"{base} + Pi context {context.provider_reference}"
    return base


class NotConnectedPiProvider:
    """The only provider in this build. Every call reports that Pi is not connected."""

    name = "not-connected"

    def whoami(self) -> PiIdentity:
        raise PiNotConnected(NOT_CONNECTED)

    def task_context(self, task: str, repository: str) -> PiContext:
        validate_task(task, repository)
        return PiContext("not_connected", NOT_CONNECTED)

    def finding_context(self, finding_id: str) -> PiContext:
        return PiContext("not_connected", NOT_CONNECTED)


def enabled() -> bool:
    return os.getenv("PI_ENABLED", "").strip() == "1"


def provider() -> PiContextProvider:
    # A real adapter belongs here once an OAuth tenant session is validated for
    # unattended use. Until then, PI_ENABLED changes only the reported reason.
    return NotConnectedPiProvider()


def status() -> dict:
    flag = enabled()
    return {
        "sponsor": "Pi Security",
        "connected": False,
        "enabled_flag": flag,
        "provider": provider().name,
        "endpoint": PI_MCP_URL,
        "detail": (NOT_CONNECTED + (" PI_ENABLED=1 is set, but no validated adapter exists yet."
                                    if flag else "")),
        "effect_on_decisions": "None. Pi context cannot publish a PDF or activate a rule.",
        "next_steps": [
            "Get a Pi Security account with tenant access (event page: Pi product access is not provided).",
            "Install the connector in Claude Code: /plugin marketplace add pi-sloane/claude-plugin, "
            "then /plugin install pi-security@pi-security, then sign in with OAuth.",
            "Run whoami and confirm subject, tenant and scopes.",
            "Run pi_playbook_task_query once for a concrete task and an explicit repository identifier, "
            "or pi_remediation_plan_fetch for a known finding.",
            "Implement a PiContextProvider that returns normalize_context(...) and record the reference.",
        ],
        "docs": DOCS,
    }
