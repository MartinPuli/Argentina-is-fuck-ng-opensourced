<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Corroborating a credential exposure before responding

This local synthetic experiment replaces the earlier trusted compromise flag with an actual observation and independent corroboration. An observer reads a known exposed-credential route. A separate controller fetches that exact enrolled route itself and checks the disclosed credential against the gateway's current generation before responding. Separate clients measure fictional records received and legitimate operations completed.

It contains no LLM, sponsor calls, general vulnerability scanner, government data, public deployment or host-intrusion test. It follows the adapted [AppBuilder plan](PLAN.md); no interface or mobile application is implemented.

## Run and inspect

Python 3.9+ and its standard library suffice. From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experiments/credential-exposure-response/run_experiment.py
```

The script creates fresh services for each mode, performs sequential HTTP requests, writes only `results.json` and `summary.json` here, and stops its children. Local socket binding can require sandbox permission. All listeners and clients accept only literal `127.0.0.1`; there are no external connections, redirects, proxies or tunnels. Do not expose these intentionally flawed fixtures publicly.

`protocol.json` and `workload.json` declare the same records, permissions and ordered requests for all four modes. Result files include their exact values and hashes, implementation hashes, distinct process IDs, sanitized transcripts and independently derived counts. Ephemeral ports, PIDs, fresh credential-dependent digests and response bodies' hashes vary between runs; request-level outcomes are reproducible. Credentials exist only in memory and loopback traffic, not files, environment variables, command-line arguments or logs. Known credential strings are checked against the complete serialized result before return.

## Processes and actual operations

| Process | Owns or does | Does not receive |
| --- | --- | --- |
| Application | Current A credential; intentional disclosure route; authenticated legitimate client route forwarding to gateway | Gateway administration, controller recovery or observer-report credential |
| Gateway | Fictional records, A/B permissions and active credential generations | Evaluator labels identifying misuse versus legitimate users |
| Controller | Fixed enrollment, independent HTTP corroboration, gateway administration and application repair/replacement credentials | A trusted compromise boolean or arbitrary caller-selected URL/action |
| Observer | GET of the one enrolled known route; submission of bounded digest/generation metadata | Gateway/app administration or raw access to service state |
| Verifier/harness | Sets up services; actual HTTP clients, captured attacker credentials, evaluator labels and outcome counts | It does not derive disclosure counts from a controller or service counter |

Processes are spawned separately. The app never receives the gateway administrator credential. **All processes still run under one OS user, and the harness owns privileged setup credentials. This is process separation, not a sandbox or a defense against hostile same-user code.**

The observer is read-only with respect to the app and gateway; its authenticated report may trigger the controller's preconfigured policy. Evidence contains only observation ID, target, exact origin/route, generation and a digest. The controller validates the target against enrollment, checks the current gateway generation, performs its own GET, compares the returned identity/generation/credential digest to the registry and evidence, and then executes the selected mode. It never follows an evidence-supplied destination. Generation-conditional revocation also protects against a generation change before that operation.

## Four matched modes

All modes enforce record scope from the start. A can read only owner A's records; B can read the complete 12-record batch. Every mode later provisions generation 2. Provisioning alone does not revoke generation 1.

| Mode | Response to corroborated exposure | Expected limitation |
| --- | --- | --- |
| `scope_only` | Record corroboration; no response | A stolen allowed credential remains usable. |
| `repair_only` | Disable the disclosure route | Already stolen generation 1 remains valid after generation 2 is issued. |
| `revoke_only` | Revoke the exposed generation | The unrepaired route exposes generation 2; misuse succeeds before the next observation. |
| `combined` | Revoke generation 1 and disable the route, then provision generation 2 at the declared recovery event | Pre-response disclosure and temporary legitimate A denial still occur. |

“Repair” is an authenticated deterministic switch that removes this fixture route. It is not a source-code patch, build, deployment, clean host recovery or proof of finding every copy of a credential. The final observer pass detects the renewed exposure in revoke-only and revokes generation 2. A final legitimate A read explicitly records this second interruption.

## Observed effects

The main run uses 27 ordered events per mode, five misuse requests and four legitimate A requests. There are no concurrent or in-flight requests. The observer/controller corroboration is scheduled between the second and third misuse requests; it is not a measured detector latency.

| Mode | Misuse records actually delivered | After first response | Legitimate A completed | B batches completed | Cross-owner records |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scope only | 6 | 3 | 4/4 | 3/3 | 0 |
| Repair only | 5 | 2 | 4/4 | 3/3 | 0 |
| Revoke only | 4 | 1 | 2/4 | 3/3 | 0 |
| Combined | 3 | 0 | 3/4 | 3/3 | 0 |

Each B batch returns 12 fictional records, totaling 36 transmissions and 12 distinct IDs. Misuse IDs are distinct in the main case; the result format also handles repeat transmissions separately. Three records escape before the first response in every mode. A legitimate caller using the same credential is also denied after revocation: the gateway has no way to know the caller's intent. If a replacement credential cannot be captured after repair, its scheduled misuse request still executes without a credential and receives HTTP 401; the transcript distinguishes this from revocation of a captured key.

Counts come from client-observed JSON response bodies, checked against the fictional record manifest. Response status, size and digest accompany the sanitized body. The observer/controller statements are retained as diagnostic evidence, not used as record-disclosure counters. Workload labels remain entirely in the verifier; services receive only credentials, IDs and bounded control metadata.

Declared checks cover actual misuse and availability, cross-owner enforcement, false digest, wrong target/origin, unauthenticated evidence, stale generation, conflicting/duplicate operation IDs, old-key rejection, replacement behavior and non-loopback bind refusal. These are selected deterministic checks, not an efficacy rate or a statistical trial. The plan preceded implementation; a final A read was added after initial review to expose the second revoke-only interruption, and the saved results were regenerated with that explicit workload.

The saved main run passed **88 checks**. A separately authored [independent checker](independent_check.py) passed **304 assertions across 120 HTTP read responses in eight runs** against the final implementation; its [results](independent-results.json) retain source hashes. Those cases change routes, owners, record counts, Unicode IDs and workload order, check mixed-owner requests, and exercise partial recovery failures. They share the service implementation and local OS boundary; they are additional regression evidence, not an independent product benchmark or blinded evaluation.

## Reuse and independent review

Import `run_mode(mode, protocol, workload)` from `run_experiment.py` in a normal Python file protected by `if __name__ == "__main__":`. It returns observations without writing files. Record IDs, owners, route, request sizes and event sequence are configurable; the two identity names A/B are fixed. The main `verify` function intentionally expects the declared main case; changed cases should have independently specified assertions.

`start_service(kind, config, context=None)` returns a process and its origin/PID metadata; `stop_services(processes)` cleans up only those children. `services.request` is the bounded loopback HTTP client. These helpers permit independent controller/gateway tests without copying the main assertions. Never pass production credentials or external origins.

## Remaining limits

- Detection knows one enrolled endpoint and a fixed response schema. A different leak path, obfuscated secret, compromised observer, transient exposure or credential copied elsewhere can escape this observer. Corroboration checks accessibility and identity, not an attacker's intent or proof of record theft.
- Same-user processes, an all-powerful setup harness, plain HTTP and trusted in-memory gateway/controller state remain assumptions. There is no container, VM, OS account separation, TLS, durable audit store, rate limiter, model-injection evaluation or compromised-host recovery.
- Repair and recovery are not transactions. The gateway issues a new credential before app provisioning. If provisioning fails, generation/state can be stranded and requires trusted manual recovery. The code reports failure rather than claiming recovery; crash/retry reconciliation and orphan-credential cleanup are not implemented. Likewise, revocation can succeed before a later repair fails.
- Replay records and identity state are in memory. A controller restart loses idempotency history. Observation IDs have no cryptographic attestation or wall-clock expiry; stale generations are rejected, but no broader evidence-freshness guarantee is claimed.
- Sequential requests avoid concurrency races. There is no measured detection delay, containment propagation, throughput, outage duration, attacker adaptation or production resilience result.
- Revocation does not retract records already received. This experiment demonstrates why scope, corroboration, revocation and exposure removal have different effects; it does not establish AI benefit or universal prevention.

## License

Python source and executable JSON fixtures are MIT under `LICENSE-MIT`. `PLAN.md`, this README and generated results are CC BY 4.0. The MIT grant is limited to this directory's code/fixtures and does not relicense other project content.
