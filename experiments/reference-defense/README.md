# Local reference experiment: authorization and revocation effects

This is a reproducible **synthetic reference experiment**, not the BREACHSTOP product. It uses real loopback HTTP requests and responses, fictional records, and fresh local credentials. It contains no LLM, sponsor integration, public deployment, autonomous vulnerability discovery, or government-system testing.

## Run

Python 3.9 or newer and its standard library are sufficient. No packages or credentials need to be installed.

```sh
python3 experiments/reference-defense/run_experiment.py
```

Run from the repository root, or invoke the script by absolute path. It launches a temporary child service for each mode, binds both endpoints **only to literal `127.0.0.1`**, runs the client, writes `results.json` and `summary.json` in this directory, then stops the service. A restrictive execution sandbox may require permission to bind local sockets. The service rejects public bind addresses; do not expose it through a tunnel or reverse proxy.

Each run creates new A, B and control credentials; replacement credentials are also newly generated. They travel through process pipes or loopback requests and remain in memory. They are not command-line arguments or saved configuration. Credential-bearing control responses are redacted before results are written. All records are visibly fictional.

## Protocol

`contract.json` declares the owner map, the intended access permissions, allowed response actions and the naive threshold. `workload.json` declares the complete ordered workload. Every mode receives the same contract and workload, with different fresh credential values. Their hashes accompany every result.

| Mode | Data-access behavior | Reaction to separately supplied compromise event |
|---|---|---|
| `no_containment` | Valid credential permits requested records; missing owner-scope enforcement. | None. |
| `naive_volume` | Same missing scope enforcement; more than three requests per identity in a trailing ten-tick window returns HTTP 429. | None. |
| `scope_only` | Owner permissions and explicit batch permission enforced. | None. |
| `scope_and_revocation` | Same permissions as `scope_only`. | Controller revokes A generation 1 through the authenticated control endpoint. |

The scientifically useful comparison for **revocation** is `scope_only` versus `scope_and_revocation`. Adding missing access control must not be described as an AI improvement. The naive cutoff is deliberately simple and its threshold is declared; this is not a representative evaluation of all anomaly detectors.

The scenario contains thirty records across three fictional owners. A is allowed Alice's records; B is an explicitly authorized batch identity allowed all three owners. Seven B requests each request the full thirty-record batch. A's stolen credential makes slow requests inside its permitted scope. Separate negative probes request Bob's records. A malicious telemetry string requests expanded permissions and revocation of B; it is stored strictly as untrusted text.

At the declared confirmation event, the external scenario controller supplies a confirmed compromise of A generation 1. Only the revocation mode reacts. A legitimate caller then uses exactly the same old credential and is also denied: containment has an availability cost. A replacement credential is issued later in every mode. Issuance alone does not revoke older credentials. The workload checks the original credential again, exercises the replacement, and submits stale, expired, duplicate and conflicting response commands.

Time is a **logical clock**, advanced by an authenticated controller call. Ticks are not measured seconds. Requests are sequential and awaited, so there are no in-flight races in this experiment. Before/after exposure is classified by event order, including when events share a tick. Confirmation and replacement ticks are extracted from their event types. No real detection latency, throughput or production time-to-containment claim follows from this protocol.

## Independent observation

The client runs in a different process from the service. It counts IDs extracted from actual HTTP response bodies, validates them against the fictional manifest, and retains response status, body, size and digest. It never reads the server's exposure counters or accepts the controller's claim that a record was blocked. Both record transmissions and distinct delivered IDs are reported; repeated batches are not thirty new people each time.

Evaluator labels such as `credential_misuse` and `legitimate` are **not sent to the data service**. The service sees a credential and a record request. It cannot distinguish a legitimate caller from an attacker holding the same credential. Thus within-scope misuse succeeds until revocation, including in the scope-enforced modes. The supplied compromise event, not a secret request-classification oracle, enables the response.

`results.json` holds sanitized response transcripts, per-mode metrics, declared checks and source hashes. `summary.json` is the compact machine-readable result. Checks cover the intended access boundary, pre-confirmation exposure, post-revocation denial, A's interrupted legitimate request, B continuity, replacement behavior, control authentication and response-command replay rules. These are checks of this declared scenario, not a statistical success rate.

For independent variants, import `run_mode(mode, contract, workload)` from `run_experiment.py`; it returns a result without writing files. The `verify` function intentionally contains fixed-main-scenario assertions. Independently changed workloads should supply their own expected assertions. `main()` overwrites only the two named main-result files, not additional variant artifacts.

Three independently specified variants and six additional runs are provided in `independent_variants.py`. Run `python3 experiments/reference-defense/independent_variants.py` from the repository root to regenerate `independent-results.json`. This verifier checks response bodies without using the main assertion function or summary counters. It covers changed record names/counts, request sizes, an extra scope probe, ordering and logical timing. It uses the same HTTP runner and service implementation; it is additional regression evidence, not a blinded AI evaluation. The plain-English [measured effects report](../../docs/research/MEASURED-EFFECTS.md) explains both sets of results and their limits.

## Boundaries and limitations

- The data and control endpoints share **one child process and one in-memory state object**. Their separate ports and credentials provide logical separation only. They are not separate protection domains, containers, operating-system accounts or a defense against compromise of this service process.
- The evaluator and child run as the same operating-system user. The evaluator holds both application and control credentials. This is a test harness, not an enforced least-privilege deployment or a file-isolation demonstration.
- `confirmed_compromise` is trusted, externally supplied scenario evidence. The service does not independently corroborate or authenticate the underlying incident evidence represented by `source_event_id`. It authenticates the command's control credential and checks contract revision, generation, time and idempotency. Detection and trustworthy incident confirmation remain unimplemented.
- No model reads the malicious log text. The test establishes only that this program's telemetry endpoint cannot directly mutate permissions. It does **not** measure LLM prompt-injection resistance.
- Scope enforcement prevents cross-owner access immediately. It cannot identify misuse within the stolen identity's valid scope. Records delivered before revocation remain exposed; revocation cannot retract copies.
- Revoking A also blocks legitimate A operations using the old credential. B continuity and later replacement success do not erase A's containment interruption. The experiment does not measure elapsed downtime.
- Credential issuance does not constitute code repair, clean deployment, root-cause removal or recovery from a compromised host. The fixture performs none of these actions.
- The toy record service uses bearer tokens, an in-memory store and a controlled clock. It lacks production TLS, durable audit storage, retries, independent policy administration, evidence attestation and crash recovery. Authorization tests and response replay checks cover selected paths, not complete security.
- The ordered fixture and modest data set are intentionally controlled. There is one main run per mode. No generalization, significance, broad threat coverage or AI-caused improvement is established.

## License

Python source and executable JSON fixtures (`contract.json`, `workload.json`) are MIT licensed under `LICENSE-MIT`. Documentation and generated result artifacts in this directory are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), consistent with the research documents. This directory's MIT grant does not relicense other project files.
