# ArgenSec Gate

A set of agents that checks every PDF before PAMI, Argentina's national health insurer for retirees and pensioners (about 5 million members), publishes it, so patient files stop reaching the public web.

## What it does

PAMI local offices upload PDFs to public purchase records. ArgenSec Gate checks each PDF before it can reach the public portal. Rule-based detectors, Spanish OCR and two AkashML models look for personal and medical data. Clean files are published. Wholly clinical or identity files are kept private. When patient details can be removed, Guild agents decide what each clearance level may see, the app deletes the details from the PDF, and a cleaned copy is published only after a Guild reviewer and the detectors both agree it is clean. Anything uncertain is restricted automatically, with a one-line note from a Guild agent. No upload waits for a person, and people audit the outcomes afterward. On the Review page, a person can release an automatic restriction with a written reason, or keep it private. A rule-based block can never be released. This autonomous mode runs behind a flag (`GATE_AUTONOMOUS=1`), which is on for the live site. In a measured run there, 9 of 9 files finished without a person in 68.5 seconds: 2 published, 3 cleaned, 4 withheld. With the flag off, uncertain files wait for a person instead. The public route checks the decision again on every download, and public files get neutral names. The Live page shows an agent log with links to each Guild session, and a step timeline with durations for each file.

## Why it matters

In May 2026, [Chequeado](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/) found that PAMI's public purchasing site exposed medical histories, disability certificates and copies of ID cards. A sample of early-2026 purchases held at least 40 cases. Removal took about two weeks. The files were published because nothing checked them first. ArgenSec Gate is that check.

## How the agents work

- Rule-based detectors run first, with no model. They catch national ID (DNI) numbers, personal tax IDs (CUIL, validated by check digit), PAMI affiliate numbers, birth dates, home addresses, ICD-10 diagnosis codes, disability certificates and ID card copies. Company tax IDs are allowed, since supplier data is public on purpose.
- Scanned pages are read with Spanish OCR and an AkashML vision model.
- An AkashML text model reads the document. It flags re-identification risk, such as age plus town plus hospital, and returns the exact phrases that point to a person.
- Rules learned from documented incidents also run. Each rule is tested on fictional examples, then a reviewer activates it, then stored files are rechecked.
- For files that can be cleaned, the Guild clearance loop runs. An orchestrator agent classifies each piece of information as clinical, procurement or public. A public agent lists the exact text to remove for the public level. The app removes it from the PDF for real and reruns the detectors. A public review agent reads only the cleaned copy and answers PASS or FAIL. On FAIL its feedback goes back to the public agent, up to 3 rounds. If it still fails, the file is restricted automatically.
- Models can only add caution. A rule-based block is final. A missing or failed check keeps the file private. Nothing is published by default.

## Sponsor tools

- **ClickHouse:** data storage and analysis at PAMI scale. It holds the audit log of every decision, plus 1,000,000 clearly labeled simulated history events. The History page (`/dashboard`) runs live queries on them: unsafe uploads by UGL (PAMI's local offices), by data type, by month, and files affected by a rule update. Each shows its measured query time.
- **AkashML:** inference. An open text model (`openai/gpt-oss-120b`) reads each file for re-identification risk and lists exact phrases to remove. A vision model (`Qwen/Qwen3.8-27B`) reads scanned pages.
- **Semgrep:** reviewed the AI-written code. [Issue #2](https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced/issues/2) reports findings and fixes. Semgrep's first scan ([raw output](https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced/blob/main/gate/semgrep/initial-scan.json)) found that the review forms had no CSRF protection, so any website could make a signed-in reviewer approve a held medical file. We fixed it with a same-origin check and a test. The later scan's findings were false positives. Our own review found two more bugs, in rechecks and public files, now fixed.
- **Guild.ai:** runs the agent procedure. An orchestrator agent classifies information into three clearance levels (clinical, procurement, public). A public agent lists what to remove so the document conforms to the public level. The app redacts it. A public review agent checks the cleaned copy and sends feedback back to the public agent until it passes (max 3 rounds). Otherwise the file is restricted automatically. A reviewer-note agent writes a note for each held file. The app drives the loop, because native sub-agent calls did not trigger. Every step runs as its own Guild session. The app polls only the agents' answers and runs at most four Guild calls at once, so a batch of files does not time out.

## Links

- Repo: https://github.com/MartinPuli/Argentina-is-fuck-ng-opensourced (app in `gate/`)
- Live site: https://argensec.pujia.ar (on Live, `/live`, choose "Test data > Load synthetic files")
- Video: [VIDEO LINK]

All demo documents are fictional. No real patient data is used.

## Team

- Nico: [NAME], [EMAIL]
- Martin: [NAME], [EMAIL]
- John: [NAME], [EMAIL]

## Short version (60 words)

ArgenSec Gate keeps patient files off PAMI's public purchasing site. Rule-based detectors and AkashML text and vision models check every PDF. Guild agents sort information into clinical, procurement and public levels, then loop until a cleaned public copy passes review. Otherwise the file stays private automatically. ClickHouse logs every decision and analyzes a million simulated events. Semgrep found a CSRF hole, now fixed.
