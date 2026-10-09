# Advanced & Current Best Practices

This file covers ecosystem-level practices beyond the design system itself - the kind of decisions that separate a "works on my phone" build from a production-grade one. Sourced from current (2026) React Native / Expo ecosystem guidance; re-verify version-specific claims with a search if this file is more than a few months old, since this ecosystem moves fast.

## Architecture & runtime
- **New Architecture (Fabric + TurboModules + JSI) is the default**, not an opt-in, as of recent React Native releases - don't disable it "for safety" on a new project; the old bridge is being retired industry-wide and staying on it is now the exception, not the safe choice.
- **Hermes is the default JS engine** in modern Expo projects and should stay enabled for every production build - faster cold start, lower memory, smaller bundle.
- If animations regress after enabling the New Architecture (a known transitional issue), check the current Reanimated performance guide for the specific mitigation flags rather than downgrading Expo SDK or Reanimated versions to "fix" it - downgrading trades a temporary regression for a permanent dead end.

## Lists
- **`FlatList` is fine under ~50 items.** Between 50-500, either works. **Above ~500 items, use `FlashList`** (Shopify's recycling list) - it reuses rendered cells instead of destroying/recreating them, which is the structural fix `FlatList` can't retrofit.
- Whichever list component is used, always supply a stable `keyExtractor` and, for `FlatList`, `getItemLayout` when row height is knowable in advance - this alone removes a large class of scroll jank by skipping runtime measurement.
- Keep list rows presentational - push data-fetching and heavy derived computation up to the parent/hook, not inside each row. Rows with their own async work or excessive local state are the most common cause of list performance complaints, independent of which list library is used.
- For extremely large or chat-style inverted lists where even `FlashList` shows edge-case flashing, note that newer recycler-based alternatives exist - worth a quick check at build time rather than assuming `FlashList` is automatically still the best fit for every new project.

## Animation
- Animate on the **UI thread, not the JS thread** - use `useNativeDriver: true` for the classic `Animated` API, or prefer Reanimated for anything more complex than a simple opacity/transform tween. Never drive a scroll-linked or gesture-linked animation from JS-thread state updates.
- A janky animation is almost always a thread-blocking problem, not a "need a faster device" problem - profile before guessing.

## Data fetching & caching
- Prefer a dedicated data-fetching/caching layer (e.g. TanStack Query) over ad hoc `useEffect` + `useState` fetch logic once an app has more than a couple of screens sharing the same data - it removes duplicate in-flight requests, gives you cache invalidation on mutation, and removes a large class of "stale data after navigating back" bugs for free.
- Parallelize independent network calls (`Promise.allSettled`) rather than sequential `await`s when the results don't depend on each other.

## Type safety
- Even in a JavaScript-first codebase, keep a `tsconfig.json` with `checkJs` enabled so the editor/IDE still catches type errors in `.js` files via JSDoc-inferred types - this is a low-cost way to get most of TypeScript's safety benefit without a full migration, and it's a reasonable default for any new project even before deciding whether to fully adopt `.tsx`.
- For a genuinely new project (not migrating an existing large JS codebase), defaulting to TypeScript from the start avoids ever needing this incremental step.

## Bundle size & startup
- Route-based code splitting (dynamic `import()` per navigator route) keeps the initial JS bundle limited to what the first screen needs, rather than the whole app.
- Audit imports for accidentally-bundled large libraries (a common cause: importing an entire icon library's default export instead of individual icons) - this is a frequent, easy win for cold-start time.
- Clean up all listeners, timers, and subscriptions on unmount - a leaked interval or event listener is a silent, compounding performance and memory cost, and is one of the most common review findings in mature codebases.

## Over-the-air updates
- **EAS Update** lets JS-only changes (bug fixes, copy changes, most UI tweaks) ship to users without an app store review cycle - set this up from the start of a new project, not after the first urgent post-launch bug. Anything touching native code (a new native module, permission entries, an SDK version bump) still requires a full store submission; EAS Update can't patch those.
- Pin each release channel to a specific native build so an OTA update never gets served to a binary it wasn't tested against - a JS update assuming a newer native API than the installed binary has is a silent, hard-to-diagnose crash source.
- Have a rollback plan (a previous update group to revert to) before pushing any OTA update, the same way you'd want a rollback plan for a server deploy.

## Image handling
- Prefer `expo-image` over the core `Image` component for anything beyond the simplest static asset - it gives disk+memory caching, better placeholder/blurhash support, and more predictable loading behavior across platforms than the legacy `Image`.
- Request images sized for their actual display size (via a resizing CDN parameter, or Supabase Storage transform options if available) rather than downloading a full-resolution original into a 100×100 thumbnail slot - this is a frequent, easy win for both bandwidth and scroll performance in any image-heavy list or grid.
- Always set explicit `width`/`height` (or aspect ratio) on an image before it loads, so surrounding layout doesn't jump once the image resolves - this is the image-specific case of the general "reserve space before content arrives" rule that also governs empty-state gating.

## Gesture handling
- Use `react-native-gesture-handler` (paired with Reanimated for the resulting animation) for anything beyond a simple `onPress` - swipeable rows, drag-to-reorder, custom bottom sheets, card-stack swipe interactions. The core `PanResponder` API is legacy and noticeably less smooth for anything gesture-driven.
- Gesture-driven interactions should be interruptible - a user beginning a new gesture mid-animation should feel the animation respond immediately, not finish playing out before accepting new input. This is a common polish gap between "looks like a demo" and "feels native."

## Code quality & CI
- ESLint + Prettier configured from the first commit, not retrofitted once the codebase is large enough that a full-repo reformat becomes its own disruptive PR.
- A pre-commit hook (e.g. Husky + lint-staged) that runs lint/format on staged files catches most style issues before they reach a PR, cheaper than catching them in review.
- Even a minimal CI check (lint + a build/typecheck step) on every PR catches a meaningful fraction of "works on my machine" issues before they reach `main` - this doesn't need to be elaborate to be worth having from day one.

## Monitoring & observability beyond crashes
- Crash reporting (see app-lifecycle-essentials.md) catches hard failures; it doesn't catch a screen that's technically not crashing but is slow, janky, or silently failing a network call. Add basic performance monitoring (frame-drop rate, JS thread stall duration, cold-start time) through the same tool used for crash reporting where possible, rather than a second, uncorrelated system.
- Track key funnel events (signup completed, core action completed) even at a minimal level from day one - reconstructing "when did drop-off start happening" retroactively from a launch with no instrumentation is far harder than adding a few event calls up front.

## Deep linking & universal links
- Configure both the custom URL scheme (`myapp://...`) and, for anything meant to work from a web-shared link, platform universal/app links (iOS Associated Domains, Android App Links with a hosted `assetlinks.json`) - a custom scheme alone won't open from a plain web link tapped in Messages/Mail on either platform.
- Validate and sanitize any data extracted from a deep link before using it to navigate or query - a deep link is user-controllable input from outside the app and should be treated with the same suspicion as any other external input, not trusted implicitly because it "came from our own share flow."

## Accessibility beyond the baseline
- Respect the OS-level "reduce motion" accessibility setting - swap non-essential decorative animations for an instant or simple-fade equivalent when it's enabled, rather than forcing every user through the full animation regardless of their system preference.
- Support OS-level dynamic type / font scaling preferences at least at a basic level - text that becomes unreadable or overlapping when a user has increased their system font size is an accessibility failure independent of the app's own responsive-scaling system (see design-tokens.md), which handles device *size* differences, not user *preference* differences.
- Periodically test primary flows with the platform screen reader (VoiceOver on iOS, TalkBack on Android) - the accessibility baseline in components.md (roles, hit targets, labels) is necessary but not sufficient without an actual pass through the app with a screen reader enabled.

## Font & splash loading strategy
- Hold the splash screen visible (`expo-splash-screen`'s `preventAutoHideAsync`) until custom fonts have finished loading via `useFonts`, then hide it - never let the first frame render with a fallback system font before custom fonts swap in, which produces a visible flash-of-unstyled-text on launch.
- Treat font-load failure as a real error path (log it, fall back to a system font gracefully) rather than leaving the splash screen stuck indefinitely if a font asset fails to load.

## Folder structure at scale
- Feature-based/domain-based grouping (screens + hooks + components co-located per business domain) scales better than a strict `components/`, `hooks/`, `screens/` split once an app has many distinct product areas - but for a single-product app like the shape described in `file-structure.md`, the flatter domain-agnostic split is simpler and sufficient. Reassess toward feature-based grouping only when a top-level folder (e.g. `screens/main/`) starts accumulating files that clearly cluster into unrelated sub-domains.
- Keep folder depth to 3-4 levels; more than that is a sign a feature deserves its own top-level slice rather than deeper nesting.

## Living documentation
- Keep a `PROJECT_SUMMARY.md` at the repo root that a new contributor (human or agent) can read in under two minutes to understand: what the app does, the current architecture shape, and where the source of truth for design tokens and schema lives. Update it in the same session as any structural change - a stale summary is worse than none, because it actively misleads.
- Keep a `QUICKSTART.md` with the exact copy-pasteable commands to get a fresh clone running locally (install, env vars, run) - don't assume tribal knowledge.

## When starting a genuinely new project
Given the above, the default recommendation for a brand-new app in 2026 is: Expo with the New Architecture and Hermes on by default (no action needed, just don't disable them), TypeScript from the start if there's no legacy JS codebase to migrate, FlashList reserved for any list expected to exceed roughly 500 items, Reanimated + gesture-handler for anything beyond simple opacity/transform animations, `expo-image` over the core `Image` component, EAS Update configured from the start for JS-only patching, a dedicated data-fetching/caching library once more than a couple of screens share server state, and lint/format/CI wired up before the codebase grows past a size where retrofitting them becomes its own project.
