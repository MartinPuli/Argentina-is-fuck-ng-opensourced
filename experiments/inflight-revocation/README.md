# In-flight revocation: actual streamed and queued output

This local synthetic experiment measures a narrow question: **does revoking a credential also stop records from requests admitted earlier?** In the saved run, admission-only authorization still delivered four records after revocation acknowledgment. Checking the admitted generation at every protected output boundary delivered zero of those later records. Both modes had already delivered one stream record, which neither can retract.

This is a research backend, not the BREACHSTOP product, an attack detector, or a paper reproduction. It is motivated by the action-time barrier discussion in [RRR-01](../../docs/research/REVOCATION-AND-RECOVERY-RESEARCH.md#rrr-01), whose complete protocol is not implemented here. No LLM, sponsor service, real credential, personal data, public host or external connection is involved.

## Run and inspect

Requires Python 3.9+ with its standard library. From the repository root:

```sh
python3 -B experiments/inflight-revocation/run_experiment.py
```

The command starts two short-lived child processes bound only to `127.0.0.1`, executes both modes against the same declared fixture, verifies results and replaces only this experiment's `results.json`. The operating environment must permit loopback sockets and child processes. Never expose the endpoints through a tunnel, proxy or public bind. Startup rejects any configured non-loopback bind.

- [PLAN.md](PLAN.md): pre-implementation AppBuilder plan adapted to the research backend.
- [protocol.json](protocol.json): fictional records, workload, prefix length and ordering.
- [gateway.py](gateway.py): gateway and controller; reusable `start_service`/`stop_services` and bounded HTTP helper.
- [run_experiment.py](run_experiment.py): actual client measurements and checks; reusable `run_case(mode, protocol)` writes no files and accepts changed owners, record IDs/content, batch lengths and prefix size.
- [results.json](results.json): complete sanitized run evidence, client observations, ordering, process IDs, source/workload hashes and 77 passed assertions.

The parent reviewer owns `independent_check.py` and `independent-results.json` if added. Independent review is not claimed by this initial result.

## Protocol and authorization boundary

Both modes validate a fresh bearer credential and every requested record's owner at admission. A and B have separate credentials, identities and records. Credentials and queued-job capabilities remain in memory; they are not written in fixture/result files, process arguments or logs. The HTTP client, gateway and controller have distinct process IDs. The controller has a fixed enrolled identity and its own command credential; only it receives the gateway's separate administrator credential. A separate coordinator credential controls experiment barriers and grants no record permission.

1. A and B complete ordinary authorized reads. An A job is accepted with HTTP 202 but its worker waits on an explicit event.
2. A streaming request is admitted. The independent client reads exactly the declared prefix of complete NDJSON record lines. The gateway then confirms its stream is paused at a server event.
3. The controller requests revocation. Under the gateway's output mutex, the gateway marks A inactive, advances its generation and writes/flushed its acknowledgment. The controller waits for that response before sending its own ACK, which the client reads in full.
4. Only after that ACK does the client release the paused stream and queued worker. The client reads the remaining stream bytes and asks for the completed job's result.
5. A new ordinary A read is rejected; B's independent batch still succeeds. A repeated stale revocation receives HTTP 409. Child processes are stopped in a `finally` block.

The declared prefix is a deterministic scheduling aid, not attacker detection. Waiting for explicit events establishes happens-before ordering; socket/event timeouts only fail stalled tests. There are no sleeps used to establish the result, and no detection or response-latency claim.

The queued-result endpoint represents completion of an already admitted operation. It is accessed through a fresh per-job capability bound to the stored admission context. Admission-only mode deliberately does not re-authorize that context. The other mode checks the stored identity/generation before every protected output line. Treating the job as a new ordinary A read instead would hide the specific stale-admission problem being tested. Its worker performs a small digest computation after release; no substantial asynchronous workload is claimed.

## Observed effects

Numbers are from the saved two-run experiment, with one prefix record, two suffix records, two queued records, one-record ordinary A reads and three-record B batches. The two modes have identical normalized workload hashes. Denominators describe this fixture only.

| Client-observed outcome | Entry-only check | Per-output generation check |
|---|---:|---:|
| Stream records received before ACK | 1 | 1 |
| Protected NDJSON line bytes before ACK | 96 | 96 |
| Remaining stream records received after ACK | 2 | 0 |
| Queued records received after ACK | 2 | 0 |
| Total later protected record transmissions | 4 | 0 |
| Later protected NDJSON line bytes | 385 | 0 |
| All later stream/job response body bytes | 425 | 114 |
| Ordinary legitimate A requests succeeding | 1/2 | 1/2 |
| Ordinary legitimate B requests succeeding | 2/2 | 2/2 |
| B record transmissions across both batches | 6 | 6 |

The 114 bytes in the stricter mode are two denial markers. Zero protected bytes does **not** mean zero network traffic. Protected line bytes include each entire UTF-8 NDJSON record line, including its JSON envelope and newline; counts exclude HTTP headers, transport overhead and non-record markers. Metrics count transmissions, not unique people or unique records.

The client measures received bodies and exact fixture content rather than accepting controller record counters. Results retain observed record bodies/IDs, response status, byte lengths, SHA-256 body hashes and event order. The gateway's ACK sequence is supporting diagnostic data, not the source of the measured effect. The harness verifies exact records, A/B availability, denial markers, barrier ordering, distinct processes and cleanup.

The admitted A stream can itself be legitimate work: the stricter mode interrupts it after its prefix, and suppresses the admitted queued result. Revocation cannot distinguish legitimate and malicious users of the same credential. The separate A availability measurement makes that cost explicit; no replacement or recovery is attempted here.

## Limits and interpretation

- **Already emitted bytes cannot be recalled.** The prefix is deliberately read in full before ACK, and the remaining output is withheld by test barriers. This does not establish that a client on a real network receives no bytes after an ACK: bytes previously written into socket, proxy or network buffers may arrive later.
- The tested boundary serializes the generation check, each protected line's write/flush and gateway ACK under one lock. This prevents a new protected line from beginning after this gateway's revocation boundary in the stricter mode. Separating check from write, bypassing the lock, adding an unmediated output path or trusting another sink would reintroduce check/write races. It is not a proof about arbitrary gateways.
- A write already inside the lock completes or fails before revocation can acquire that lock and acknowledge. Slow output can delay revocation. B can also experience transient contention on the shared lock; the experiment measures eventual B success, not latency or isolation of performance.
- A flush is a local write boundary, not proof that every remote receiver consumed or erased bytes. The deterministic barriers avoid an uncontrolled mid-write race; exhaustive concurrent interleavings, partial socket-write failures and large buffered payloads are not tested.
- Revocation is explicitly requested by the trusted test client. Compromise detection, evidence corroboration, autonomous decisions, delegated credentials and provider acknowledgment authenticity are outside scope.
- The gateway and controller are separate processes under the same OS user, not isolated security sandboxes. The gateway contains data and enforcement and is assumed trustworthy. A compromised gateway/host can bypass this experiment's controls.
- Credential generations, jobs and decisions exist only in memory. Restart durability, stale replicas, retries across crashes, cancellation fan-out, recovery, replacement credentials and real provider side effects are not implemented. Process cleanup is measured; authorization persistence is not.
- This is an application-line stream over HTTP/1.0 connection-close responses, not HTTP transfer-encoding chunks or token streaming. The general output-boundary concern motivates the test; no external application or paper benchmark is reproduced.

Code and protocol fixtures: [MIT](LICENSE-MIT). Documentation and saved results: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
