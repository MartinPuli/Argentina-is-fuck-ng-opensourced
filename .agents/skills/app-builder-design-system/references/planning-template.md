# Planning Template

Produce this as a markdown doc (in-chat or as a file, per the request's context) before writing any screen or component code for a new app or major feature. Fill in every section - an empty section is a sign a decision was skipped, not that it doesn't apply.

Sections 0 and 1 are produced once, up front, for the whole idea. Sections 2 onward are produced per-phase - write Phase 1's in full detail before building it, then repeat sections 2 onward for Phase 2 when its turn comes, and again for Phase 3. Don't fully spec Phase 2/3 details before Phase 1 is built - a one-paragraph forward-look is enough for phases not yet being built.

```markdown
# <App/Feature Name> - Build Plan

## 0. Who this is for
- Target user(s):
- Their current problem / what they do instead today:
- What "solved" looks like for them:
- Scope: frontend only for now, or frontend and backend together?

## 1. Three-phase breakdown
| Phase | Theme | Features included | Forward-look detail level |
|---|---|---|---|
| 1 | Core loop - smallest version that lets the target user complete the central task end to end |... | Full detail (sections 2+ below) |
| 2 | Completeness - what turns Phase 1 into something people keep using |... | One-paragraph summary until Phase 1 ships |
| 3 | Depth & delight - differentiation, polish, retention, edge cases |... | One-paragraph summary until Phase 2 ships |

Every feature mentioned in the original idea/request must appear in exactly one phase row above. If a feature doesn't obviously belong, ask the user which phase it's for rather than guessing.

---
# Phase <N> detailed plan

## 2. Backend
Skip this whole section if section 0 marked this project (or this phase) as frontend only - note "no backend for this phase" and move to section 3. Screens build against local state or mock data instead; leave a one-line note on roughly where a future backend would hook in, so adding one later is an addition, not a rebuild.

### Tables
| Table | Key columns | Notes |
|---|---|---|
|... |... | e.g. FKs, uniqueness constraints |

### RLS policies
For each table: who can SELECT / INSERT / UPDATE / DELETE, and under what condition.
Flag any bidirectional-consent visibility (see backend-patterns.md) explicitly.

### RPCs needed
| RPC | Purpose | Why not a direct client query |
|---|---|---|

### Storage buckets
| Bucket | Public/private | Signed URL expiry | What's stored |
|---|---|---|---|

## 3. Screen inventory
| Screen | Purpose | Owner-view or viewer-view (if applicable) | Data source (hook) |
|---|---|---|---|

## 4. Navigation flow
Describe the flow as a short list or simple diagram: onboarding sequence, tab structure, how detail screens are reached and what params they need.

## 5. Component needs
For each screen, list any NEW component needed (not already in the catalog) and its required states (default/disabled/loading/error/empty) per components.md.

## 6. Edge cases to handle explicitly
Go through patterns-and-edge-cases.md and note which apply to this phase:
- [ ] Platform share differences (if a share action exists)
- [ ] Safe area nesting (if a screen embeds another full screen)
- [ ] Multi-image picker batching (if photo upload exists)
- [ ] Empty states needed (list which screens)
- [ ] Form validation / leave-without-saving guard (if a multi-field form exists)
- [ ] Responsive type/spacing check on narrowest supported device

## 6b. Architecture & performance checklist
Per advanced-practices.md, decide these explicitly rather than defaulting silently:
- [ ] Any list expected to exceed ~500 items? → use FlashList, not FlatList
- [ ] Any animation beyond simple opacity/transform? → Reanimated, UI-thread driven
- [ ] More than 1-2 screens sharing server state? → dedicated fetch/cache layer, not ad hoc useEffect
- [ ] New project with no legacy JS to migrate? → default to TypeScript from the start

## 6c. Lifecycle & pre-launch checklist
Per app-lifecycle-essentials.md - decide and record each of these, even if the answer is "not needed yet":
- [ ] Env/config: dev vs prod Supabase projects set up as separate EAS build profiles?
- [ ] Any camera/photo/notification permission → all three states (not-yet-asked, denied-can-retry, denied-blocked) handled?
- [ ] Crash reporting configured from day one?
- [ ] Localization: single-language for now, but strings kept in a lookup table rather than hardcoded inline?
- [ ] Testing: is this feature high-consequence enough (payments, bookings) to warrant unit tests on the business logic?
- [ ] Push notifications: needed for launch, or explicitly deferred?
- [ ] Offline behavior: does this flow need to work with no network, or is a blocking "you're offline" state acceptable?

## 6d. Security checklist
Per security-and-data-protection.md - every phase that touches auth, storage, or new tables. Not applicable if this phase is frontend only:
- [ ] Every new table has RLS enabled in the same migration that creates it?
- [ ] Any elevated-privilege RPC has its own explicit authorization check inside the function?
- [ ] No service-role or other elevated key anywhere in client code or an `EXPO_PUBLIC_*` var?
- [ ] Tokens/session data confirmed routed through secure storage, not AsyncStorage?
- [ ] Auth-adjacent endpoints (login, OTP) rate-limited server-side?
- [ ] Any new third-party SDK checked against what it collects and whether that's reflected in the privacy policy?

## 6e. Store publishing checklist (once shipping is in view)
Per store-publishing-checklist.md - flag these during phasing, don't discover them at submission time:
- [ ] Account deletion (in-app, real deletion) planned into the phase that adds account creation
- [ ] Privacy policy and store privacy labels planned to be kept in sync with actual data collection
- [ ] Android: if this is a new personal developer account, 12-tester/14-day closed testing lead time built into the release schedule

## 6f. Motion & delight checklist
Per animation-and-motion.md:
- [ ] Every new animation traced to a named duration + easing/spring token, not an invented one-off value
- [ ] Anything gesture-driven (drag, swipe, sheet) uses springs, not fixed-duration timing - and stays interruptible
- [ ] Any rare/milestone moment in this phase checked against the Delight Moments catalog - is it under-designed for how much it matters, or over-designed for how often it repeats?
- [ ] Reduced-motion equivalent considered for any new slide/spring/parallax motion
- [ ] If this is Phase 3 work, confirm celebratory/bouncy treatment is reserved for genuinely rare moments, not applied broadly

## 7. Open questions for the user
Anything genuinely ambiguous that changes the plan meaningfully - ask before building, don't guess and rebuild later.
```

## When to skip parts of this
- Tiny, single-screen, no-new-table changes (e.g. "add a filter option to Discover") don't need the full backend section, and often don't need a fresh 3-phase breakdown if they clearly slot into an existing phase of an in-progress app - just note "no schema change" / "fits into existing Phase N" and move to screens.
- A frontend-only project or phase skips section 2 entirely, and sections 6c/6d largely don't apply - say so plainly rather than leaving them blank with no explanation.
- If the user has clearly pre-approved the whole plan in a prior message, skip re-presenting it and go straight to build - but still produce sections 0-1 internally/silently (know who it's for, know the three phases, know the scope) and still follow the backend → hooks → screens sequencing (when there's a backend) within whichever phase is being built.
- Any section can be answered with "skip for now" at the user's request - record it as deferred, not resolved, so it surfaces again if it becomes relevant later.
