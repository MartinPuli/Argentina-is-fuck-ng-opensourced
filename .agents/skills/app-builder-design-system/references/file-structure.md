# File Structure

A general folder shape for a React Native / Expo app with a Supabase backend, reflecting how a real production app in this style actually grows past the initial scaffold. Adapt naming to the specific app's domain, but keep this overall shape.

```
<root>/
├── App.js
├── app.json
├── babel.config.js
├── metro.config.js
├── eas.json # EAS Build/Submit config
├── tsconfig.json # even in a JS-first codebase, keep this for editor
│ type-checking of.js files (checkJs) - see advanced-practices.md
├── vercel.json # only if the app also ships an Expo web build
├── README.md
├── QUICKSTART.md # copy-pasteable setup steps for a new dev/agent
├── DEPLOYMENT.md # EAS build/submit steps, env var checklist
├── PROJECT_SUMMARY.md # living one-page "what is this app" doc - see advanced-practices.md
│
└── src/
 ├── brand/ # Design tokens - single source of truth
 │ ├── Colors.js
 │ ├── Typescale.js # FontFamilies, FontSizes, LineHeights, Type, FONT_SCALE, scaleSpace
 │ ├── Spacing.js # Space[n] scale
 │ ├── Radii.js # Radius[n] scale - kept separate from Spacing once a project has enough
 │ │ distinct corner-radius needs (cards vs pills vs sheets)
 │ └── index.js # re-exports Colors, Space, Type, Radius
 │
 ├── components/ # Shared, reusable across screens - see components.md for the full
 │ │ catalog and the required states for each
 │ ├── index.js # barrel export - screens import `{ Button, Input, Modal }` from one place
 │ ├── <domain>/ # feature-scoped component sub-folder, e.g. profile/, checkout/
 │ │ └── <Feature>Card.js
 │ └── *.js # flat for genuinely cross-cutting components (see components.md)
 │
 ├── screens/
 │ ├── auth/ # sign up / log in / verification, pre-account
 │ ├── onboarding/ # multi-step account/profile setup, post-signup pre-main-app
 │ ├── main/ # primary tab/stack screens once onboarding is complete
 │ ├── edit/ # "edit my X" screens reached from main, one file per editable section
 │ └── public/ # screens reachable without auth (public share links, viewer mode)
 │
 ├── navigation/
 │ └── Navigation.js # root navigator - stacks/tabs, linking config, auth-state routing
 │
 ├── hooks/ # one hook per data domain, wraps Supabase calls
 │ ├── use<Domain>.js # e.g. useProfile, useOrders, useMessages
 │ └── use<Domain>Derived.js # pure derivation from state (no fetching)
 │
 ├── store/ # global state (Zustand or equivalent)
 │ └── <domain>Store.js
 │
 ├── lib/ # thin wrappers around external services
 │ ├── supabase.js # client init
 │ └── tabReselect.js # example: pub/sub for "tab tapped while active" → scroll to top
 │
 ├── utils/ # pure functions, no React, no external service calls
 │ ├── shadows.js # platform-select shadow/elevation helper - see design-tokens.md
 │ └── map<Domain>FromDB.js # DB-row → client-model normalizer - see advanced-practices.md
 │
 └── constants/
 └── options.js # dropdown option lists, enums, etc.
```

## Why `navigation/` sits outside `screens/`
The root navigator config (stacks, tabs, linking, auth-gated routing) is infrastructure, not a screen - keeping it as a sibling of `screens/` rather than nested inside it makes it obvious at a glance where routing logic lives, especially once the screens folder is split into `auth/onboarding/main/edit/public` sub-folders.

## Why a `utils/` folder distinct from `lib/`
- `lib/` = thin wrappers around an external service or cross-cutting app-level concern (the Supabase client, a pub/sub bus).
- `utils/` = pure, stateless functions with no side effects and no imports from React or a service SDK (a DB-row mapper, a shadow-style generator, a date formatter). This split matters because `utils/` functions should be trivially unit-testable in isolation; if a "util" needs a mock of Supabase to test, it belongs in `lib/` or a hook instead.

## Rules for placing new files
- A component used by 2+ screens → `components/`, exported through the barrel `index.js`. A component used by exactly 1 screen and unlikely to be reused → keep it inline in that screen file, don't over-extract prematurely.
- A `use*` hook wraps exactly one data domain and owns its own loading/error state. Screens don't call Supabase directly - always through a hook.
- Pure derived-value logic (formatting, computing a display string from raw data) lives in a `use<X>Derived` hook (if it depends on component state) or a plain `utils/` function (if it doesn't), never inline in JSX.
- A raw Supabase row is never passed directly into a component's props - always pass it through a `map<Domain>FromDB.js` normalizer first, even if the mapping is currently a near-identity function. This is what lets the DB schema evolve (column renames, added nullable fields) without touching every screen that consumes that data.
- Global state is for things genuinely needed across unrelated component trees (auth session, badge counts read by a tab bar). Don't reach for global state for screen-local UI state (a modal's visible/hidden flag stays in that screen's local state).
- Keep folder depth shallow - 3-4 levels is the sweet spot; if a sub-folder needs its own sub-folders to stay organized, that's usually a signal the feature deserves a top-level slice of its own rather than deeper nesting.
- Keep this file structure doc updated in the same session as any structural change to a real project, so it doesn't silently drift from what's actually built.
