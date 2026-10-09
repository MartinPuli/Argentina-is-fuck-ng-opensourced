# Security & Data Breach Prevention

Apply this to every new app by default, not just apps that feel "sensitive." Any app with user accounts, personal data, or a backend has an attack surface - treat these as required, not optional hardening for later.

## The core principle: never trust the client
Every security control that matters must be enforced at the database/server layer (Supabase RLS, RPC logic), never only in client-side JavaScript. A client-side check (hiding a button, a `disabled` prop, an `if (isOwner)` in a component) is a UX convenience, not a security boundary - it can always be bypassed by anyone calling the API directly. If a piece of data or an action must be restricted, there must be an RLS policy or RPC-level check enforcing it, independent of whatever the UI does or doesn't show.

## Secrets & key management
- The Supabase **anon key** is safe to ship in the client - it's designed to be public, and RLS is what actually protects data behind it. The Supabase **service-role key** (or any key that bypasses RLS) must **never** appear in client code, a client bundle, an `EXPO_PUBLIC_*` env var, or a git-committed file - it belongs only in a server-side context (a Supabase Edge Function, a separate backend), never anywhere the client can read it.
- Any third-party API key with a paid quota or write access (payment processor secret keys, transactional email provider keys) is server-side only, for the same reason - a client-embedded key with real quota/privileges is a standing invitation to abuse.
- Scan for accidentally-committed secrets before every push - a pre-commit secret-scanning hook (e.g. gitleaks) catches an `.env` file or a hardcoded key before it reaches a public or even private remote history that's hard to fully scrub after the fact.
- `.env` files are always gitignored; commit an `.env.example` with variable names but no real values instead, so a new environment setup knows what's needed without exposing what the values are.

## Authentication & session security
- Store session tokens in secure, encrypted storage (`expo-secure-store`, backed by iOS Keychain / Android Keystore) - never `AsyncStorage`, which is unencrypted plain storage on both platforms and readable by anything with device/file access.
- Invalidate sessions server-side on logout, not just by clearing local storage - a token that's merely "forgotten" client-side but still valid server-side is still usable if it leaked before logout.
- Rate-limit authentication-adjacent actions (login attempts, OTP requests/resends, password reset requests) at the backend - an unlimited-attempt login or OTP-resend endpoint is a standing invitation to brute-force or spam abuse. A Supabase RPC or Edge Function fronting these actions can enforce a cooldown/attempt cap that a client-side "disable the button for 30 seconds" cannot actually enforce.
- Never log full tokens, session objects, or passwords - not even in development-only `console.log` calls that could ship if a debug flag is accidentally left on in production.

## Row Level Security (RLS) discipline
- Every table has RLS enabled from its first migration - a table created "temporarily" without RLS and fixed later is a common real-world breach vector, because "temporarily" often outlives the intention.
- Write policies as narrowly as the use case allows - a policy that grants broader access than the current feature needs "in case it's useful later" is exactly the kind of latent over-permission that turns into a breach once a new feature accidentally exposes it.
- Any RPC that runs with elevated privileges (`SECURITY DEFINER`) must do its own explicit authorization check inside the function body - elevated-privilege functions bypass RLS by design, so the function itself becomes the entire security boundary for whatever it touches.
- Re-run the project's security advisor/linter (see backend-patterns.md) after every schema change - a new table or a changed policy is exactly when a missing-RLS or overly-permissive-policy issue gets introduced.

## Input handling
- Treat all client-supplied input as untrusted, including values from deep links, share-flow parameters, and anything round-tripped through the client even if it originated from the app's own backend - validate shape and range server-side (RLS conditions, RPC parameter checks), not just client-side form validation, which only prevents accidental bad input, not deliberate bad input.
- Parameterize all queries (the Supabase client does this by default for standard queries) - never construct raw SQL by string-concatenating user input, even inside an RPC or Edge Function.

## Third-party SDK & dependency hygiene
- Every third-party SDK (analytics, ads, crash reporting, social login) is a data-collection surface you're responsible for even though you didn't write its code - know exactly what data each SDK collects and whether it matches what your privacy policy and store privacy disclosures claim (see store-publishing-checklist.md).
- Run dependency vulnerability scanning (`npm audit`, or an automated tool like Dependabot/Renovate keeping dependencies current) on a regular cadence, not just at initial setup - a vulnerability disclosed after a dependency was added doesn't announce itself; the scan has to be re-run.
- Prefer the minimum SDK footprint that satisfies the actual requirement - every additional third-party library is both an attack surface and a data-sharing relationship, not a free feature.

## Data minimization & user rights
- Collect only the data a feature actually needs, not data that "might be useful later" - the smallest data footprint is both the safest default and the easiest to keep privacy disclosures accurate against.
- Support account and data deletion as a real, complete operation (not a soft "deactivate" flag) - both a functional requirement (see store-publishing-checklist.md, this is enforced by both app stores) and a genuine data-protection practice: a user who deletes their account should have their personal data actually removed or irreversibly anonymized on a reasonable timeline, not just hidden from the UI while remaining fully intact in the database.
- Encrypt sensitive data at rest where the platform doesn't already guarantee it, and rely on TLS (which Supabase and virtually all modern backends enforce by default) for data in transit - verify this isn't accidentally downgraded by any custom networking configuration.

## Optional hardening for higher-sensitivity apps
Not needed for every app, but worth a deliberate yes/no decision (and recorded as such) for anything handling payments, health data, or similarly sensitive categories:
- **Certificate pinning** - protects against man-in-the-middle interception even on a compromised network/proxy; adds operational overhead (a pinned cert rotation requires an app update) so weigh this against the app's actual risk profile.
- **Jailbreak/root detection** - can reduce (not eliminate) tampering risk on compromised devices; primarily relevant for apps handling payment credentials or similarly high-value client-side secrets.
- **Biometric re-authentication** for particularly sensitive in-app actions (viewing stored payment details, authorizing a transfer) - a stronger step-up beyond the initial session login.
