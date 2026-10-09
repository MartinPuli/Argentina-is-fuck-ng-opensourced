<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Synthetic publication regression experiment

This runnable local experiment tests whether one manually approved publication rule catches the same class of exposure after filenames, paths, extensions, records and application layout change. Public-attachment exposure is the motivation. This is **not a reconstruction of PAMI**, an AI learning demonstration, or evidence about a real organization's systems.

The rule is explicit: every source needs a classification; only approved public sources may enter a release; every built artifact must have provenance and match its approved source hash; the deployed artifact set must be exact and freshly assembled. `lesson-policy.json` records approval for this synthetic experiment under the task owner's authorization. Its approval field is a trusted input, not a signed approval or an institutional authorization workflow.

## Run and inspect

Requires Python 3.9 or later and its standard library. From this directory:

```sh
python3 run_experiment.py
```

The run creates fresh temporary staging directories, starts HTTP servers on ephemeral ports at **literal `127.0.0.1` only**, launches separate verifier processes, closes the servers and deletes only its temporary staging trees. It makes no external connections and needs no credentials, installation, container or deployment. Some execution sandboxes require approval for even a loopback listener. Public bind addresses are rejected before a server is created.

The command writes only `results.json` and `summary.json` here. Results preserve every observed status, response length, response hash, base64 response body and matched private fixture ID. `summary.json` is derived from these observations. All records and sensitive markers are fictional. Raw observations deliberately retain previously fetched private fixture bytes: stopping later publication cannot erase an earlier recipient's copy.

## Protocol

Each fixture declares public procurement summaries and private synthetic attachments. A source manifest describes their classification, source hash and output mappings. A build manifest describes what the current build claims to emit. The physical build tree and deployable output are separate directories. Manifests remain outside the served directory.

Three conditions receive the same declared unauthenticated `GET` probes:

1. **Baseline publication:** copy all sources into the build and publish its entire tree. This intentionally unsafe fixture represents a publication process that fails to enforce attachment classification.
2. **Source-only fix:** physically remove private source files and their manifest entries, then run an incremental build over the previous build cache. The build copies current sources but does not prune old output. Publishing that tree still exposes stale private files. This is an explicit, reproducible build behavior, not a simulated dashboard result.
3. **Approved release gate:** first reject that dirty build because its physical artifact set exceeds the current manifest. Then build only public sources in a fresh directory from the full classified source manifest, verify hashes and provenance, and copy the exact approved set into a new release directory.

`serve_local.py` serves every regular deployed file without authentication; it does not hide files based on classifications or sensitive filenames. `verify_http.py`, in another process, reads the actual deployment inventory and probes the union of declared paths, any additional deployed files, and optional fixture probe paths. It compares public response bytes exactly and searches **every response** for each complete private fixture payload or marker. Therefore a private payload copied into a nominally public URL is also counted. Counters do not come from the publisher or gate.

For a successful gated release, the verifier compares the release manifest's path/hash mapping to both the physical deployment inventory and the observed HTTP 200 artifact path/hash mapping. This establishes the exact canonical artifact set in this finite static fixture; it does not enumerate every syntactic URL alias that an HTTP server could accept.

Additional checks reject an unclassified source and a public artifact whose content changed after approval, with no deployment directory created. These are release failures, not HTTP denials. A deliberate false-classification counterexample appends known private content to an owner-approved public source: the gate permits it, and the independent client observes the private bytes. Manifest integrity alone cannot establish confidentiality.

## Observed effects

| Fixture and condition | Responses exposing private bytes | Distinct private sources | Public exact-content successes |
| --- | ---: | ---: | ---: |
| Initial / baseline | 4 of 6 probes | 2 | 2 of 2 |
| Initial / source-only fix | 4 of 6 probes | 2 | 2 of 2 |
| Initial / approved release gate | 0 of 6 probes | 0 | 2 of 2 |
| Changed application / baseline | 4 of 7 probes | 2 | 3 of 3 |
| Changed application / source-only fix | 4 of 7 probes | 2 | 3 of 3 |
| Changed application / approved release gate | 0 of 7 probes | 0 | 3 of 3 |

Four exposed URLs contain two underlying private sources because some outputs are aliases. Each unsafe response delivers the exact corresponding private fixture content. Private paths return 404 after the fresh gated release. The unchanged policy handles nested paths and renamed `.report`, `.svg`, `.woff2` and unknown extensions without relying on their names. These are opaque fixture bytes, not claims to generate valid image/font documents.

The two misclassification counterexamples each expose private content through one approved public URL despite matching release manifests. They are reported separately from the three-condition comparison. The main run performs 45 assertions, including this expected failure of confidentiality.

`heldout-fixture.json` changes the application layout, source IDs, contents and paths while retaining the identical policy. It is a **predeclared variation written by the experiment author**, not a blinded or independently authored evaluation. Generalization beyond these cases remains unmeasured.

## Reproducibility and independent variants

Results include SHA-256 hashes of the source code and fixture/policy files, canonical fixture and policy hashes, and each declared probe protocol. Source/build/release manifests and actual build inventories are recorded. Random staging names and ephemeral ports are excluded from persisted observations so the declared cases are deterministic.

An independent reviewer can import `run_experiment.run_case(fixture, policy)` with modified fictional source IDs, content, output paths or optional `probe_paths`. It returns structured observations and creates no persistent result files. `check_case(result, fixture)` applies the comparison assertions to a fixture whose public and private payloads are disjoint. `publisher.release_gate(...)` is also directly callable for custom artifact/manifest mutation tests. The verifier's physical inventory discovery ensures an added deployed file is probed even if its name was not in the fixture.

## Limits and what the result supports

- This supports a narrow deterministic release invariant under correct trusted labels and manifests. No model, learned scanner semantics, agent orchestration or sponsor integration is present.
- Classification and policy approval are scenario inputs. There is no semantic PII/DLP classification, authenticated owner approval or assurance against a malicious approver. The measured false-classification case exposes this limitation.
- Publisher, HTTP server and verifier are separate local processes under the same OS user and share temporary storage. This supports independent observation, not a security boundary against a compromised host or a malicious actor editing manifests and code.
- Source-to-artifact mapping is a byte-preserving copy. Real renderers, transformed attachments, remote storage, links, archives, symlink semantics and complex build systems require additional provenance and validation. The release gate rejects symlinks in its build inventory.
- The build and copy are checked sequentially in a controlled sandbox. The experiment does not establish protection against concurrent filesystem mutation, production deployment races, CDN caches or an already running compromised publisher.
- Each condition uses a separate local deployment and server. This is not a tested production cache purge or atomic live-service replacement. Old deployments, external mirrors and downloaded copies require separate response measures.
- The experiment tests the supplied paths plus the actual local artifact inventory. It makes no claim of universal prevention, recall on unknown data formats or coverage of a real breach's root cause.

Python source, `fixture.json`, `heldout-fixture.json` and `lesson-policy.json` are licensed under the adjacent MIT license. This README and generated research results are CC BY 4.0, consistent with the repository's documentation license. The MIT license here does not change the license of root documentation or other experiments.
# Additional independent check

`independent_check.py` supplies a different synthetic fixture, including Unicode and space-containing paths, changed record identifiers, different private payload sizes and public aliases. It decodes actual response bodies without using the main runner's contract checker or reported content-match counters. The persisted run in `independent-check-results.json` passed 52 assertions over 36 loopback requests.

Baseline and source-only conditions each exposed private bytes in 3/9 responses. The approved release exposed none in 9 responses and preserved all four public-file responses. Deliberately misclassified content still escaped through three public aliases. This checks the release mechanism and its limit; it is not a blinded model benchmark or production security test.
