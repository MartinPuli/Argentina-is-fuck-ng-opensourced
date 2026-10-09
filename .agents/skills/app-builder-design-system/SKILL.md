---
name: app-builder-design-system
description: Use this skill for ANY React Native / Expo app build, or any request to plan, scaffold, design, or add a screen/feature/backend table to a mobile app. General house design system and build process - audience-first, three-phase planning (understand who the solution is for, split features into Phase 1/2/3, plan and build one phase at a time), design tokens, component states, file structure, animation patterns, and Supabase backend conventions (RLS, RPC, storage). Trigger this proactively for "build me an app", "start a new app", "add a screen", "here's my idea", "what should the schema look like", "scaffold a new feature" - even without an explicit skill name mention. ALWAYS consult before writing any screen, component, or table - audience definition and phasing come before planning, planning comes before code.
---

# App Builder Design System

Every decision, made once. Made right.

Not a component library. Not a style guide.
A way of building - for anyone building a mobile product with Claude.

---

## Principles

**Know who it's for.**
Everything else follows.

**Systems, not snowflakes.**
One token. Everywhere. Change it once, and the whole product moves with it.

**Every state is a promise.**
Loading. Empty. Error. Disabled. Done means all four - not the happy path alone.

**Both platforms. Every time.**
iOS and Android are peers. Neither is the default the other has to catch up to.

**Secure the data before you design the screen.**
The backend is the contract. The frontend is the conversation. No backend yet? Say so - and mean it, not skip it by accident.

**If it moves, it means something.**
Motion is feedback, continuity, or delight. Never decoration for its own sake.

**Trust nothing the client sends.**
Protect everything the client can't see. Security that isn't invisible isn't finished.

**Nothing about launch day is a surprise.**
Shipping is a checklist. Not a hope.

**Make it work. Make it whole. Then make it unforgettable.**
Depth and delight are earned - in that order.

---

## Install

This is a [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) - instructions and reference material Claude reads before it works.

**Claude.ai / Claude apps**
Download `app-builder.skill` from [Releases](../../releases). Upload it in **Settings → Capabilities → Skills**. Start a new conversation and describe your app - no need to name the skill.

**Claude Code**
Clone this repo into your project's skills directory. Claude Code discovers any folder with a valid `SKILL.md` automatically.

**Just reading**
Every file under `references/` stands alone. Use this as a design-system reference for your own team, Claude or not.

**Build from source**
```bash
python3 -m scripts.package_skill /path/to/app-builder /path/to/output/app-builder.skill
```

---

## Start a project in five minutes

1. **Say what you want to build.** A paragraph is enough.
2. **Claude asks who it's for, and what it needs.** Who the user is, if you haven't said - and whether this is frontend only for now, or frontend and backend together. Plenty of real projects start as a prototype with no backend at all. One or two sentences back on each.
3. **Claude proposes three phases** - Core Loop, Completeness, Depth & Delight - and sorts every feature you mentioned into one. Push back on anything that feels wrong.
4. **Claude plans Phase 1 in full** - schema and RLS if there's a backend yet, screens, states, edge cases - before a line of code. Review it, or say "build it."
5. **Claude builds Phase 1, completely.** Then Phase 2. Then Phase 3.

That's the system. Everything below is what makes each step trustworthy.

**Structure, not a straitjacket.** Every step here can be skipped, for now. Say "skip the backend for now" or "no need to plan, just build" and Claude moves on, noting what's deferred rather than pretending it isn't needed. Nothing here is a gate you have to clear - it's a checklist you're always free to come back to.

---

## The build process: discover → phase → plan → code

Screen code is never the first response to a new idea. The sequence, in order, every time - and every stage can be answered with "skip that for now."

### Stage 0 - Who is this for, and what does it need
Establish the target user before any feature or schema talk: who they are, what they struggle with today, what "solved" looks like. Ask if it isn't already clear. Write it down - it's the yardstick every later decision is checked against.

Ask the scope question too: **is this frontend only for now, or frontend and backend together?** Plenty of real projects start as a click-through prototype, a portfolio piece, or an app validating an idea before any data needs to persist or sync. A backend isn't a default - it's a decision, made deliberately, for a reason. If the answer is "just frontend for now," that's a complete, valid answer, not a shortcut to apologize for.

### Stage 1 - Three phases, no exceptions
Every feature sorts into exactly one:
- **Phase 1 - Core loop.** The smallest version that lets the target user complete the app's central task, end to end. If it doesn't, it isn't Phase 1.
- **Phase 2 - Completeness.** What a real user notices missing after a week with Phase 1.
- **Phase 3 - Depth & delight.** Differentiation, polish, retention, edge cases.

A feature that doesn't obviously fit gets asked about. Never guessed.

### Stage 2 - Plan the current phase, backend first, when there is one
Two parts, using `references/planning-template.md`:
1. **Backend** - schema, RLS, RPCs, storage. Per `references/backend-patterns.md`. Skipped entirely for a frontend-only project or phase - build screens against local state or mock data instead, and note in the plan roughly where a future backend would hook in, so wiring one up later is an addition, not a rebuild.
2. **Frontend** - screens, navigation, components and states. Per `references/components.md` and `references/patterns-and-edge-cases.md`.

Only the current phase gets full detail. Later phases get one paragraph - enough to not box them in, not enough to build prematurely.

### Stage 3 - One phase at a time
Phase 1 finishes - backend when there is one, then hooks, then screens - before Phase 2 begins. No interleaving. A half-built Phase 2 next to an unfinished Phase 1 is exactly what this sequencing prevents.

"Skip planning, just build it" is respected - but Stages 0-1 still run silently, and phases still build in order. The scaffolding protects the outcome even when no one's watching it happen.

---

## What this skill takes care of

A single "build me an app" implies dozens of decisions most builders make inconsistently, if at all. This makes each of them once:

- **Product thinking** - audience and a disciplined roadmap, before any code.
- **Design system** - tokens for color, type, spacing, radius. Nothing hardcoded.
- **Components** - every primitive a real app needs, every required state.
- **Motion** - a named scale of durations, easings, springs. A catalog of what deserves delight.
- **Platform parity** - the recurring iOS/Android divergences, handled by default.
- **Backend, when there is one** - Supabase schema, RLS discipline, the RPC patterns that keep client and server honest. Never assumed, always asked.
- **Security** - the client is never trusted. Ever.
- **Production readiness** - config, crash reporting, permissions, the full current store submission checklist.
- **Engineering practice** - current best practice for lists, animation threading, data fetching, code quality.

## How Claude uses this skill

1. Read this file fully.
2. Establish audience and scope (frontend only, or frontend and backend) alongside the three-phase breakdown (Stages 0-1) before anything else - even for a single new feature on an existing app.
3. Backend in scope for this phase → read `references/backend-patterns.md` first. Frontend only → skip straight to the frontend steps below, working against local state or mock data.
4. Any screen or component → read `references/design-tokens.md` for token *structure*, then ask for (or propose) real brand values if none exist yet.
5. Any component → read `references/components.md` for its full state requirements.
6. Read `references/patterns-and-edge-cases.md` for platform gotchas, empty states, forms, sharing, safe areas, photo pickers.
7. Any animation → read `references/animation-and-motion.md` first. No exceptions.
8. New file → read `references/file-structure.md` for where it goes.
9. Any architecture or library choice → read `references/advanced-practices.md`.
10. Config, secrets, permissions, error handling → read `references/app-lifecycle-essentials.md`.
11. Auth, tokens, RLS, any RPC → read `references/security-and-data-protection.md`. Not relevant yet for a frontend-only project - revisit once a backend is added.
12. Shipping in view → read `references/store-publishing-checklist.md`, flagged during Stage 1, not submission week.
13. Any plan doc → use the exact structure in `references/planning-template.md`.

## Reference index

| File | Read when |
|---|---|
| `references/design-tokens.md` | Any style, any screen - color, type, spacing, radius |
| `references/components.md` | Building or using any core primitive |
| `references/patterns-and-edge-cases.md` | Platform gotchas, empty states, forms, sharing, safe areas |
| `references/animation-and-motion.md` | Any animation, transition, or micro-interaction |
| `references/backend-patterns.md` | Any table, RLS policy, RPC, or storage bucket - once this project has a backend |
| `references/file-structure.md` | Where a new file belongs |
| `references/advanced-practices.md` | Performance, lists at scale, data fetching, TypeScript |
| `references/app-lifecycle-essentials.md` | Config, permissions, error handling, pre-launch decisions |
| `references/security-and-data-protection.md` | Secrets, tokens, RLS, third-party SDKs - once this project has a backend |
| `references/store-publishing-checklist.md` | App Store / Play Store submission |
| `references/planning-template.md` | The plan doc format for the current phase |
