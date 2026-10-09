# BREACHSTOP sandbox architecture

Reviewed 2026-10-09. This is an architecture recommendation based on official documentation, not a runtime deployment, penetration test, or additional research-paper review. Undated documentation was read in its current form; repository `main` pages are not immutable release evidence. No production systems, leaked records, credentials, or victim files were accessed.

For the four-hour prototype, use an already available local container runtime with synthetic fixtures and a tightly bounded agent workflow. Prefer an already configured gVisor worker if compatible. Do not make installing a virtualization platform the critical path. Label the result a controlled demonstration; hostile arbitrary repositories require a stronger, validated execution boundary.

## What each option actually isolates

| Option | Boundary and trusted components | Deployment and remaining controls |
|---|---|---|
| **Firecracker** | KVM and processor virtualization separate microVMs; the host kernel, VMM, hardware, and operator configuration remain security dependencies. Production guidance calls for a jailer or equivalent restrictions, restrictive seccomp, patching, and one tenant per process. | Requires a capable Linux/KVM host and guest assets. Firecracker performs **no network filtering**: the operator must enforce guest egress, including metadata-service denial. Resource limits and hardware mitigations remain operator responsibilities. This is a production building block, not a complete repair service. [S1](https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md) |
| **gVisor** | Its Sentry implements the application system-call interface and restricts exposure to the host. Host kernel/platform, Sentry, filesystem mediation, and configured mappings remain dependencies. It does not protect files deliberately mounted into the workload or services it can reach. | External network policy and host resource limits remain necessary. Some specialized interfaces are unsupported; test the actual application and dependencies. The Docker integration uses the `runsc` runtime and requires daemon configuration/restart. A workload's `dmesg` output is forgeable and cannot attest the runtime. [S2](https://gvisor.dev/docs/architecture_guide/security/), [S3](https://gvisor.dev/docs/user_guide/quick_start/docker/) |
| **Kata Containers** | Runs containers inside a VM, with a guest kernel and agent; runtime, hypervisor, host, and shared-file implementation remain dependencies. Multiple containers in one pod can share the VM. Thus two containers do not establish two VM boundaries. | Integrates through containerd/CRI-O and Kubernetes RuntimeClass. It fits an existing compatible orchestration platform better than a fresh four-hour setup. Place mutually distrusting patch and verification workloads in separate pods/VMs; separately constrain their network and shared files. [S4](https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md) |
| **E2B, optional managed path** | Vendor documentation describes one Firecracker microVM per session. In E2B Cloud, E2B operates the control plane and Google Cloud data plane and manages storage/keys. These are additional trusted parties. | Vendor lists egress controls and several deployment options; private cloud remains in development. Embed requires Linux x86-64/KVM. Use only if an account and working integration already exist; verify selected deployment and feature availability. These are vendor claims, not independent assurance. [S5](https://e2b.dev/enterprise) |

The versioned **E2B Python SDK 2.5.0** documents `allow_internet_access=True` by default. Set and test the intended policy explicitly; a sandbox creation success does not prove blocked egress. [S6](https://docs.e2b.dev/sdk-reference/python-sdk/v2.5.0/sandbox_sync)

E2B's **October 7, 2026 Secrets announcement** describes external header injection: the proxy resolves credentials after requests leave the sandbox. It explicitly warns that environment-variable secrets remain readable by sandbox code. BYOC support was still forthcoming in this announcement. Our inference: hiding a key reduces theft but does not authorize the requests made with it; constrain destinations, operations, scope, and budgets independently. [S7](https://e2b.dev/resources/introducing-e2b-secrets)

Docker's own guidance identifies kernel, daemon, configuration, and capability risks. Controlling the daemon can permit arbitrary host mounts; namespace isolation and resource limits serve different purposes. For the prototype, keep daemon control outside the agent and remove unneeded capabilities. Containers alone are not evidence that a repair agent cannot leak accessible data. [S8](https://docs.docker.com/engine/security/)

## Three separate jobs

The following is our proposed design, not a capability demonstrated by these sources.

1. **Patch preparation:** a fresh workspace receives a pinned source snapshot, sanitized incident evidence, and synthetic records. The agent may edit application files. It cannot modify the launch policy, trusted test bundle, or controller. Return a diff, base/candidate hashes, and bounded execution logs. Do not give this worker a GitHub write token, cloud administrative credential, production database connection, home directory, or container socket.
2. **Attack rehearsal:** start disposable baseline and candidate applications from independent snapshots. A controlled attacker client can reach only these synthetic services. Execute the same predefined unauthorized-access cases and record observable responses. Keep this network separate from production and from the host administration interfaces.
3. **Independent verification:** a fresh worker receives the candidate artifact by hash and a fixed evaluator from a trusted source. Run both denial tests and legitimate-use tests. The patcher cannot write the evaluator or declare its own success. Treat candidate build scripts as untrusted too: keep verdict collection and the evaluator controller outside their execution boundary.

A trusted coordinator owns job creation, policy selection, artifact transfer, test collection, and any later PR creation. The agent receives narrow operations through a controller; it cannot grant itself authority. A separate production containment controller remains necessary: patch execution isolation does not revoke a live credential or stop an already exposed database.

## Four-hour implementation target and later path

**Now:** use curated synthetic code and records; prebuild dependencies; disable unnecessary outbound traffic; run as an unprivileged user with no added capabilities, a read-only base filesystem, one writable temporary workspace, and explicit time, memory, process, and output limits. Use distinct workers for the three jobs even when they reuse one image. Preserve only reviewed artifacts; discard job state. These are acceptance requirements, not claims that this repository already implements them.

**Later:** choose gVisor, Firecracker, or Kata according to verified workload compatibility and existing operations expertise. Require one independently controlled isolation unit per job/trust domain, pinned images, external egress policy, a narrow credential broker, host maintenance, bounded telemetry, and auditable cleanup. Validate regional hosting and control-plane access before introducing government data. A microVM does not repair application authorization, prevent misuse of an allowed API, or recover data already copied by an attacker.

## Verification required before claiming isolation

Use synthetic canaries and owned test endpoints. Record the configuration and result for each check:

- Workload cannot read a host canary, container socket, controller credential, or another job's workspace.
- Internet, metadata endpoints, and management networks are denied; only explicitly permitted rehearsal or dependency endpoints work.
- Resource exhaustion ends the job within configured limits and cannot fill unbounded host logs.
- Candidate code cannot alter evaluator files, reported verdicts, launch policy, or the trusted artifact hash.
- A planted instruction in an incident log cannot cause permission expansion or controller execution.
- Unauthorized requests fail after the patch while authorized requests still pass; repeat from a fresh snapshot.
- Provider/runtime identity is checked by the trusted coordinator, not by strings printed inside the workload.

None of these runtime checks was executed during this documentation review. The next deliverable should be measured pass/fail evidence, not an unqualified “secure sandbox” badge.
