# What the local experiments actually demonstrated

**Run date:** October 9, 2026. This measures deterministic controls in a synthetic reference system. It is not an AI benchmark, government pilot, sponsor integration or deployed BREACHSTOP product.

## The practical result

Ordinary record permissions blocked access to another owner's records. They could not distinguish the legitimate owner of a credential from an attacker using that same credential inside its permitted scope. Once the experiment supplied a confirmed compromise event, revocation stopped subsequent access with that credential. A different, explicitly approved batch account continued operating. The affected account's legitimate caller was also interrupted.

These outcomes came from actual local HTTP response bodies. The server was not told which requests were labeled malicious by the evaluator. The confirmation event was a trusted scenario input, **not a detection made by an AI agent**.

## Main workload

All four modes received the same ordered workload and declared permissions, with fresh credentials per run. It included thirty fictional records, seven requests using a stolen credential within its allowed scope, two cross-owner probes, four legitimate requests for A and seven authorized batch requests for B. Every B batch requested the same thirty records; repeated transmissions are not additional people.

| Control mode | Records delivered through the 7 within-scope misuse requests | Records delivered through 2 cross-owner probes | B batch requests completed | A legitimate requests completed |
|---|---:|---:|---:|---:|
| No containment, missing scope checks | 7 | 20 | 7/7 | 4/4 |
| Simple request-volume cutoff, missing scope checks | 6 | 10 | 4/7 | 3/4 |
| Ordinary scope checks | 7 | 0 | 7/7 | 4/4 |
| Scope checks plus revocation on supplied confirmation | 3 | 0 | 7/7 | 3/4 |

The two cross-owner probes requested the same ten records. Therefore 20 transmissions in that column means ten distinct fictional records returned twice, not twenty distinct victims.

The useful comparison for revocation is the last two rows: both already enforce ordinary access permissions. With scope checks alone, four post-confirmation misuse requests still succeeded. With revocation, none returned records. **Three fictional records had already escaped before confirmation.** The additional denied legitimate A request is a real availability cost within the fixture.

The old credential was tried three more times after replacement access was issued. It remained unusable in the revocation mode and remained usable with scope checks alone. Issuing a replacement is not the same action as revoking the old credential.

All **34 declared checks** passed in the main run. These include actual denial, permitted batch continuity, interrupted A access, replacement behavior and selected duplicate/stale/expired command cases. This is a count of checks, not a security success percentage.

Source artifacts: [protocol and runnable experiment](../../experiments/reference-defense/README.md), [main response transcripts](../../experiments/reference-defense/results.json), [structured summary](../../experiments/reference-defense/summary.json), [declared workload](../../experiments/reference-defense/workload.json).

## Additional independently specified cases

A separate verifier changed the initial fixture after implementation and inspected HTTP bodies without calling the main fixture's assertion function or trusting its summary counters. It tested renamed owners/record IDs, a changed record count, shifted clocks, larger per-request selections, an added unauthorized full-batch attempt, slower timing and different initial request ordering.

| Additional scenario | Post-confirmation misuse transmissions with scope only | With scope plus revocation | B batch completion in each mode | Legitimate A requests denied by revocation |
|---|---:|---:|---|---:|
| Renamed records and shifted clock | 4 | 0 | 7/7 | 1 |
| Larger requests and extra scope probe | 12 | 0 | 7/7 | 1 |
| Slower pace and reordered initial requests | 4 | 0 | 7/7 | 1 |

The six additional runs checked **122 HTTP read responses**. Every independent assertion passed. These are additional regression cases authored after the first implementation, not a blinded trial or a statistically representative sample. Repeated fictional record IDs are counted as transmissions in this table.

[Independent verifier](../../experiments/reference-defense/independent_variants.py) · [Sanitized observations and source hashes](../../experiments/reference-defense/independent-results.json).

## What follows—and what does not

The observed benefit is the effect of **explicit access control and credential revocation under the declared conditions**. No LLM participated. The simple volume cutoff's poor result is specific to its chosen threshold and this workload, not evidence that every anomaly detector fails. A future agent must show additional value over these ordinary controls.

Time advances through logical ticks, not elapsed seconds. The experiment establishes neither detection speed nor real-world time to containment. Requests finish sequentially, so concurrent or already-running exports remain untested. The data and control endpoints share a process and memory; the evaluator runs as the same operating-system user. This does not prove isolation from a compromised host.

In the original reference-defense experiment, no code repair, deployment, evidence corroboration, cryptographic log protection, sponsor calls, automatic lesson promotion, publication checking or third-party export control was exercised. The malicious log string was only stored; because no model interpreted it, this is not a prompt-injection robustness result.

For Argentina, these results demonstrate a mechanism that could limit **additional access through a confirmed compromised credential** when an institution can enforce that boundary. They cannot retract earlier copies, establish the causes of disputed incidents, quantify national losses avoided or support a percentage reduction in future government leaks.

## Additional credential-exposure experiment

The [credential-exposure response experiment](../../experiments/credential-exposure-response/README.md) removes the supplied compromise flag. A read-only observer requests one known enrolled route; a separate controller independently fetches it and corroborates the exposed credential against the gateway's current generation. App, gateway, controller and observer are separate processes, while the evaluator records actual HTTP responses. All still share one OS user: this is not a sandbox or compromised-host defense.

All four modes start with the same record permissions and later receive replacement access. In the main workload:

| Response | Misuse records received | Received after first response | Legitimate A operations | B batches |
| --- | ---: | ---: | ---: | ---: |
| Scope only | 6 | 3 | 4/4 | 3/3 |
| Remove exposure only | 5 | 2 | 4/4 | 3/3 |
| Revoke only | 4 | 1 | 2/4 | 3/3 |
| Revoke and remove exposure | 3 | 0 | 3/4 | 3/3 |

Removing the route leaves the stolen credential usable. Revoking without removing the route lets a replacement leak; the next observation revokes it again and interrupts A a second time. The combined mode blocks later misuse and restores A, but three records escaped earlier and one legitimate A operation was denied. Each B batch returns the same twelve fictional records; 36 transmissions are twelve distinct records, not 36 people.

The main run passed **88 declared checks**. A separately authored [checker](../../experiments/credential-exposure-response/independent_check.py) changes routes, owners, record counts, Unicode identifiers and request ordering. Its eight runs passed **304 assertions over 120 actual read responses**, including mixed-owner denial, false-claim rejection, stale/duplicate evidence and continued B access. These are selected regression cases, not a representative prevention rate. [Main observations](../../experiments/credential-exposure-response/results.json) · [Independent observations](../../experiments/credential-exposure-response/independent-results.json).

Here, “repair” is a trusted switch disabling the fixture route, not an agent-written patch or verified release. The observer knows the route and response format; it is not a general leak detector. Requests are sequential and observation times are scheduled. No detection latency, AI contribution, sponsor integration, public deployment, transactional recovery or protection from hostile same-user code is established. Issuing a replacement before app provisioning can strand state on partial failure; the experiment reports failure rather than proving crash recovery.

## Next measurements for the product

1. Measure the time and reliability of obtaining trustworthy compromise evidence under both malicious and legitimate traffic.
2. Deploy separate protected enforcement and evaluation components, remove bypass routes, and test concurrent requests, controller failure and recovery.
3. Demonstrate actual agent investigation, code repair, built-asset exposure removal and exact-revision deployment through three sponsor integrations.
4. Compare the agent against the deterministic baseline, including incorrect interventions, preserved legitimate work, cost and repair quality.
5. Turn a reviewed incident into a new test, evaluate unseen variations with and without that lesson, then show narrowly scoped transfer to another service.
6. Add separate acceptance scenarios for employee misuse, public attachments and recipient exports before claiming broader coverage of the Argentina report.
# Additional publication-boundary experiment

The [publication regression experiment](../../experiments/publication-regression/README.md) addresses a separate leak mechanism: private attachments accidentally becoming public files. Its main run passed 45 assertions. Both tested layouts exposed four private-content responses before the gate, including after a source-only fix; fresh approved releases exposed none while preserving the expected public content.

An independently specified fixture then checked 36 actual HTTP responses and passed 52 byte-level assertions. Its approved release preserved four public responses and exposed no private marker. A deliberate false “public” classification still leaked private bytes. Thus exact artifact checking works only within its classification assumptions; it does not establish automatic understanding of medical documents.

All traffic was loopback, records were fictional, and no sandbox escape, government host, AI repair, sponsor integration or public deployment was tested. See the linked protocol and persisted observations for denominators and limitations.
