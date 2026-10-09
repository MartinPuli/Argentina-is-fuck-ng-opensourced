<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Can a reviewed exposure check transfer to a changed service?

This local synthetic experiment shows a narrow transfer: a mechanism check catches an exposed service credential at a renamed route and nested JSON field, where the original-path-only check misses it. It also preserves a harmless public-metadata service and records two unsupported cases that remain exposed.

**The lesson is explicitly authored by the code-writing assistant and pinned by the harness as a simulated owner-review precondition. No actual institutional approval, autonomous learning or automatic rule generation is demonstrated.** The lesson transfers a described and implemented check, not a source credential or permission to mutate every service.

There are no LLMs, sponsor integrations, public listeners, real personal records or external connections. The [plan](PLAN.md) adapts the user-selected AppBuilder template to this research backend; no product UI or mobile application is implemented.

## Run

Python 3.9+ and its standard library suffice. From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/lesson-transfer/run_transfer.py
```

The runner reuses the previous experiment's gateway, bounded HTTP client and process helpers without modifying them. It creates fresh loopback services and credentials for each run, writes only `results.json` and `summary.json` here, and cleans up its child processes. Some execution sandboxes require local socket permission. Every listener and client requires literal `127.0.0.1`; do not expose or tunnel these fixtures.

The saved run passed **129 checks** across one source positive control and eight target case/mode runs. Result artifacts include code/dependency/fixture hashes, the complete lesson and fixtures, sanitized HTTP observations, status/size/body hashes, distinct process IDs and record counts derived from actual responses. Raw credentials are redacted and checked absent before results leave the runner. Ephemeral ports, PIDs and credential-dependent digests vary between runs.

## What transfers, and what authorizes action

`lesson.json` declares source/provenance, the credential-exposure mechanism, applicable response shape, bounded safe test, simulated review status and one allowed action. The source run actually fetches an exposed fictional credential, uses it to receive a fictional record, and confirms that the original check works there. The lesson is already authored; that observation does not create or train it.

For each target, a separately configured controller receives an owner enrollment containing the exact service origin, allowed route inventory, service identity, action and approved lesson digest. The submitted lesson's `approved` string grants nothing. Changing its action, applicability, provenance or adding a target invalidates the pin. A new service needs its own enrollment even when it uses the same lesson.

The observer scans only that inventory. Its mechanism implementation collects at most 32 string candidates from a JSON object, up to depth 4, without depending on credential field names. It submits paths and digests, not the raw candidate strings. The separate controller re-fetches the enrolled route, checks that the candidate really appears at that path, and compares its digest to the gateway's current active credential for this enrolled service. Only a match permits generation-conditional revocation. It does not try candidate credentials against the record API.

The original-path baseline uses only the source route and field, and only if that route is enrolled. Main target inventories include the old path as an authorized check returning HTTP 404 and, where applicable, the new route. Consequently, the comparison tests a changed check over a supplied inventory; it does not demonstrate discovery of previously unknown routes.

## Matched cases and actual effects

Fresh A/B credentials, records and HTTP workloads are matched between modes. Before checking, the test client obtains a value from the fixture's actual response and attempts an A record read. The fixture's capture path is evaluator knowledge and is never supplied to the observer/controller. A harmless public value is attempted too and receives HTTP 401. Evaluator labels identifying misuse versus legitimate use stay in the harness.

| Target case | Post-check records: original path | Post-check records: mechanism | Legitimate A completions: original / mechanism | Interpretation |
| --- | ---: | ---: | --- | --- |
| Renamed route, nested credential field | 1 | 0 | 3/3 / 2/3 | Check transfers; revocation interrupts the affected legitimate identity too. |
| Harmless public token-like metadata | 0 | 0 | 3/3 / 3/3 | Formatting alone does not establish a live credential; no false block in this case. |
| Exposure outside enrolled route inventory | 1 | 1 | 3/3 / 3/3 | Deliberate coverage gap; neither check broadens enrollment. |
| Credential in unsupported top-level JSON array | 1 | 1 | 3/3 / 3/3 | Declared representation limit; no general secret-recognition claim. |

One record is delivered before checking in each actually exposed target case; that copy cannot be retracted. B completes both authorized three-record batches in every run. The separate public notice remains accessible. These are small sequential cases, not population-level false-positive or prevention rates. There is no repair, replacement or elapsed downtime measurement in this module; the earlier experiment covers their distinct effects.

Six invalid evidence submissions run before the legitimate check: an added instruction field, an unenrolled target, and four changed lesson variants. They are rejected, and a subsequent legitimate A request proves the probes did not revoke it. The changed application's JSON also contains text asking to ignore policy and revoke B; it is treated as an ordinary string candidate. This measures deterministic schema/hash/allowlist enforcement, not LLM prompt-injection resistance.

## Reuse and independent review

`transfer.run_case(mode, case, fixtures, approved_lesson, candidate_lesson=None)` returns observations without writing files. The approved lesson establishes the harness's trusted pin; `candidate_lesson` is separately supplied untrusted evidence. Passing a changed candidate while retaining the approved lesson permits independent mutation tests. `start_surface`, the reused `start_service`/`stop_services`, and `fetch` support direct HTTP checks. Use a normal Python script guarded by `if __name__ == "__main__":` because services use spawned processes.

The main assertions are intentionally tied to the declared cases. A separately authored [checker](independent_check.py) now specifies ten further cases in both modes, changes owners, record order and quantities, and compares exact returned record bodies without importing the main assertions or summary function. Run it with `PYTHONDONTWRITEBYTECODE=1 python3 experiments/lesson-transfer/independent_check.py` from the repository root.

Its **20 runs passed 520 assertions over 140 actual gateway read responses**. The mechanism check contained three changed exposures: a four-level object, a Unicode field and an unchanged route with a renamed field. Each affected A completed 2/3 legitimate requests, while B completed 2/2 batches. A harmless lookalike did not cause revocation. Five representation/enrollment gaps remained exposed: depth five, a nested array, a credential after 32 earlier candidates, a 129-character key, and an unenrolled route. A changed rule version was also denied by the owner's pin, leaving the exposure open rather than accepting unapproved authority. These misses and the interrupted legitimate requests are part of the result, not failed assertions hidden from the report.

[Independent observations](independent-results.json) retain exact fixtures, expectations, response bodies and source hashes. Both evaluators reuse service/process code; neither is a blinded or external laboratory evaluation. The main runner never overwrites these independent files.

## Limits

- Source and target fixtures were constructed for this comparison. The target route/field is absent from the source lesson, but this is not a blinded or representative evaluation of novel real-world services.
- Transfer relies on a preimplemented JSON-string mechanism, a known owner inventory and a trusted gateway registry. It does not infer arbitrary new mechanisms from prose or historical reports. Encodings, arrays, deeper objects, excessive candidates, undiscovered paths and non-JSON documents can escape coverage.
- App, gateway and controller run in separate processes, but all share one local OS user. The privileged harness creates their configurations and credentials. This is not a hardened sandbox, independent-host attestation or compromised-host defense.
- The real-review and durable policy lifecycle are unimplemented. The hash pin demonstrates a deterministic authorization boundary under trusted enrollment; it does not authenticate an actual institution or reviewer. An unverified Argentine incident remains contextual evidence, not mutation authority.
- Revocation affects legitimate and malicious holders alike. The public exposure route is left unchanged here, and already captured records remain exposed. No complete recovery or universal prevention is established.
- Calls are sequential. No concurrency, detector latency, capacity, production availability, adaptive opponent, AI benefit or sponsor execution is measured.

## License

Python and executable JSON fixtures are MIT under `LICENSE-MIT`. Documentation and generated results are CC BY 4.0. Reused prior files retain their existing MIT license; this module does not relicense the rest of the repository.
