# App Lifecycle Essentials: Config, Security, Permissions, Errors

These are the practices that don't show up until an app is close to real users, and are expensive to retrofit if skipped at the start. Apply all of these to any new app by default - they aren't optional polish.

## Environment & config management
- Never hardcode API URLs, keys, or environment-specific values directly in source. Use `.env` files (via `react-native-dotenv` or Expo's built-in `EXPO_PUBLIC_*` env var convention) and load them through a single `config.js`/`env.js` module that the rest of the app imports from - never `process.env.X` scattered across files.
- Maintain **at least two environments** (development, production) as separate EAS build profiles in `eas.json`, each pointing at its own Supabase project/keys. Never point a development build at the production database "just for now" - this is how test data ends up in production and vice versa.
- Any value that's genuinely secret (service-role keys, private API secrets) never ships in the client bundle at all - `EXPO_PUBLIC_*` variables are compiled into the app and are as readable as any other client code. Secrets belong server-side (a Supabase Edge Function, RPC, or separate backend), never in an env var prefixed for client exposure.
- Keep an up-to-date checklist of required env vars in `DEPLOYMENT.md` so a fresh environment setup isn't guesswork.

## Secure storage
Auth tokens and session data go in `expo-secure-store`, never `AsyncStorage` - see `security-and-data-protection.md` for the full secrets, storage, and session-security discipline (that file is the source of truth for anything security-related; this file covers config/permissions/error-handling only).

## Permissions UX
Every permission request (camera, photo library, notifications, location) needs the same three-state handling, not just a bare "ask and hope":
1. **Not yet requested** - trigger the request only at the moment the user takes an action that needs it (tapping "Add Photo"), never on app launch speculatively.
2. **Denied, can ask again** - show a clear in-app explanation of why the permission is needed before re-prompting, don't just silently re-fire the system dialog.
3. **Denied, can't ask again (blocked)** - the system dialog won't reappear; the app must detect this state and offer a deep link to the OS settings screen for the app (`Linking.openSettings()`), with copy telling the user exactly what to toggle.
A permission flow that only handles state 1 is incomplete - states 2 and 3 are where real users actually get stuck.

## Error handling & crash reporting
- Wrap the app root in an error boundary that shows a recoverable "something went wrong" screen instead of a blank white/black screen on an uncaught render error.
- Integrate a crash/error reporting service (Sentry is the common default for RN/Expo) from the start of a new project, not after the first production crash report comes in via app store reviews. Configure it to capture: unhandled JS exceptions, unhandled promise rejections, and native crashes.
- Every `try/catch` around a network call should do something a user can act on (a retry button, a specific error message) - a bare `console.error` with no UI feedback is a dead-end error handler and should be treated as a bug, not a stub to fill in later.
- Distinguish expected failures (no network, invalid input, permission denied) from unexpected ones (a genuine bug) in both the UI copy and what gets sent to crash reporting - don't send every network timeout to the error tracker as if it were a crash.

## Decisions to make explicitly, even if the answer is "not yet"
These don't need to be built into every app, but the decision should be made and written down during planning, not silently skipped:
- **Localization/i18n** - is this app single-language at launch? If yes, still avoid hardcoding user-facing strings directly inline in a way that would require a full rewrite to extract later - a simple `strings.js` lookup object costs almost nothing now and saves a rewrite later.
- **Testing** - for a small/early-stage app, manual QA on both platforms before each release may be sufficient; for anything with payment flows, multi-step forms, or backend logic with real consequences (bookings, transactions), at least a thin layer of unit tests on the business logic (not full E2E) is worth the cost.
- **Push notifications** - if planned for later, at minimum register the device token capability early (it requires a paid Apple Developer account and provisioning setup that's easier to sort out before launch than after).
- **Offline behavior** - decide explicitly whether core flows must work with no network (show cached data, queue actions) or whether a simple "you're offline" blocking state is acceptable for this app's use case. Don't leave this undecided - an app that silently fails on poor connectivity with no messaging is a common source of "the app is broken" reviews that are actually a network-handling gap.
- **App store submission** - see `store-publishing-checklist.md` for the full iOS + Android requirements list; note in planning which of those items are already handled vs. still open, well before the first submission attempt.
