# Cyberdefense Hackathon — project constraints

**Recorded:** October 9, 2026
**Authority:** Latest event text supplied and reaffirmed by the user in this conversation.
**Event:** Cyberdefense Hackathon, San Francisco, Friday October 9, 2026.
**Timezone:** Pacific time, America/Los_Angeles.

This is the event brief for the Argentina data-leak project. Preserve these requirements when refining the architecture or implementation. It supersedes earlier assumptions that sponsor integrations were optional. Requirements from the earlier AWS and personal-agent hackathons do not apply.

## Required challenge fit

- Build defensive AI that discovers threats, understands attacks or helps fix vulnerabilities.
- Build an autonomous agent that performs real work on the open web.
- The agent must take real action, such as publishing, monitoring, orchestrating or transacting.
- Ground its work in truthful sources.
- Use **at least three sponsor tools** in substantive, demonstrable ways.
- Establish the application context before the agent writes or changes anything: what it needs to understand, which security boundaries changes could affect and which decisions must be explicitly defined rather than guessed.
- Build the project during the event.
- Submit one project per team, with at most four people per team.

The user's additional preferences remain: open-source project, focus on Argentina's data-leak problem, and a substantial solution. Project documents remain in English; current discussion and pitches are in Spanish at the user's request. Open-source licensing is the user's requirement; the pasted event submission text requires reviewer repository access, not specifically a public license.

## Submission

- GitHub repository accessible to reviewers.
- Short demo video with a shareable link.
- Explanation of what was built and which tools were used.
- Team members' names and contact email addresses.
- Working website and screenshot are welcome but optional submission assets.

No maximum video length, official presentation duration, general scoring weights or prize-stacking rule is established by the supplied text. Do not invent these.

## Schedule

| Milestone | October 9, Pacific time |
|---|---|
| Doors | 9:30 AM |
| Kickoff and hacking | 11:00 AM |
| Portal opens, according to the supplied page | 11:30 AM |
| Lunch | 1:30 PM |
| **Submission deadline** | **4:30 PM** |
| Demos and judging | 5:00 PM |
| Awards and closing | 7:00 PM |

## Sponsor tools and prizes

| Sponsor | Role and supplied award terms |
|---|---|
| **ClickHouse** | Real-time analytics. Judged on data scale, query/response latency and direct contribution to detection, remediation or monitoring. First: $1,000 Amazon/Visa gift card plus $500 credits. Second: $500 Amazon/Visa gift card plus $300 credits. Third: $250 cash/Amazon gift card. |
| **Pi** | Overall prize: $1,000 / $600 / $400 gift cards. **No product or technical access is provided at this event.** Do not count Pi as a used integration. |
| **Akash** | GPU marketplace and AkashML inference. Best-use-case prizes: $500 / $250 / $150 Akash credits. |
| **Guild.ai** | Hosting and running agents. Winning team: $1,000; two runner-up awards: $500 each. |
| **Semgrep** | Most unique or interesting vulnerability or issue found in **AI-generated code**. First: $1,000 cash gift card. Second: $500 cash gift card. Both receive 20 Semgrep credits. A deliberately seeded demo vulnerability is not automatically a qualifying discovery. |
| **Senso.ai** | Verified-context infrastructure. Best-use awards: 3,000 credits for first; 1,000 credits for second and third. Its integration must perform a real context task if counted. |

The supplied Semgrep setup uses its Guardian plugin for Claude Code, followed by restart and browser sign-in. The text identifies it as public beta with no credit card required and directs users with blocked access to Semgrep staff at the event. Setup instructions do not themselves prove a working project integration.

## Sources and verification status

- [Event portal](https://tokensand.com/cyberhack): the latest user-pasted page supplies the exact additional challenge, sponsor and submission requirements recorded here. The browsing tool could not independently retrieve this portal during the fit assessment.
- [Official Luma event](https://luma.com/cyberhack): independently read; corroborates the defensive categories, remediation/verification focus and 4:30 PM deadline. It does not independently establish every added portal requirement or detailed bounty term.
- [ClickHouse documentation](https://clickhouse.com/docs)
- [Guild documentation](https://docs.guild.ai/)
- [Semgrep Guardian](https://docs.semgrep.dev/semgrep-guardian/overview)
- [Akash documentation](https://akash.network/docs/) and [AkashML](https://akashml.com/docs/getting-started)
- [Senso documentation](https://docs.senso.ai/docs/overview)

## Implications for BREACHSTOP

The proposed required integrations are ClickHouse for incident evidence, Guild for the agent workflow and Semgrep for actual code findings. The agent must perform real bounded actions on our controlled system, with a public GitHub change and externally verified demo. Background research must not be presented as evidence that the prototype tested or repaired Argentine government systems.

The expanded design must prove containment, isolated repair and verified recovery for one complete attack chain. More integrations or diagrams do not establish a working outcome. Consult [HACKATHON-FIT.md](HACKATHON-FIT.md) for the current proposal and [process notes](../process-notes.md) for decisions and unresolved questions.
