# Store Publishing Checklist (App Store + Play Store)

Everything below should be treated as part of the build, not an afterthought bolted on right before submission - several of these (account deletion, privacy manifest, closed testing) require in-app work or lead time that's expensive to retrofit at submission time. Re-verify specifics with a search if this file is more than a few months old - both stores' policies change on a roughly annual cycle. As of this writing (2026):

## Universal requirements (both stores)

### Account deletion - required, not optional
Both Apple (since June 2022) and Google Play require that any app supporting in-app account creation **also** supports in-app account deletion - a real delete, not a "deactivate" flag. Requirements:
- A clearly reachable "Delete Account" action inside the app (typically in Settings), not buried or requiring a support email.
- Deletion must actually remove or irreversibly anonymize the user's personal data server-side within a reasonable window - see security-and-data-protection.md's data minimization section.
- Google Play additionally expects a **web-based deletion path** alongside the in-app one (a page users can reach without having the app installed).
Build this in Phase 1 or 2 of any app with account creation, not as a last-minute Phase 3 add - missing this is one of the single most common rejection reasons on both stores.

### Privacy policy - required, must match actual behavior
- A live, publicly reachable privacy policy URL, linked from both the app itself (typically Settings) and the store listing metadata.
- The policy's stated data practices must match what the app **actually does** - reviewers (and automated tooling) cross-check declared practices against observed network requests, permissions, and known SDK behavior. A mismatch (e.g. using an analytics SDK not mentioned in the policy) is a common rejection trigger on both platforms.
- Audit every third-party SDK in the build against the policy - an SDK's data collection is your disclosure responsibility even if you didn't write its code.

### Data safety / privacy labels - required, must match the policy
- **iOS:** App Privacy "nutrition label" questionnaire in App Store Connect, covering every data type collected and whether it's linked to the user's identity or used for tracking.
- **Android:** Play Console's "Data safety" section - a similar structured questionnaire (data collected, shared with third parties, whether encrypted in transit, whether deletion is supported).
- Both are re-evaluated on every new release, not just the first submission - an update that changes data collection without updating the corresponding label can get an update rejected, not just the initial app.

### App Tracking Transparency (iOS) / tracking disclosure
If the app tracks users across other companies' apps/websites for advertising purposes, iOS requires the ATT prompt before any such tracking begins, and the privacy nutrition label must reflect it. Apps that don't do cross-app tracking (the common case for most first apps) can skip the ATT prompt but should still confirm no bundled SDK (an ad network, certain analytics tools) is quietly doing this on the app's behalf.

### Support contact - required and actually checked
A working Support URL (App Store Connect metadata / Play Console listing) that a reviewer can reach from a cold browser with no login required, with an actual way to contact you. A broken or login-walled support URL is consistently one of the most common rejection reasons on iOS specifically because it's the fastest thing for a reviewer to check.

### Permission usage strings
Every permission the app requests (camera, photos, location, notifications, contacts) needs a clear, specific usage description string (`NSCameraUsageDescription` etc. on iOS via `app.json`'s `ios.infoPlist`, and the corresponding Android manifest entries, which Expo config plugins largely generate from `app.json` permissions arrays). A generic or missing usage string is a common rejection point - the description should say specifically what the permission is used for in this app, not a boilerplate placeholder.

### Store assets
- App icon: platform-specific size/format requirements (no alpha channel on the iOS 1024×1024 marketing icon).
- Screenshots for each required device size class per platform - stale screenshots that don't match the current build's UI are a metadata-mismatch rejection risk, not just a quality issue.
- A content/age rating questionnaire, completed accurately for the app's actual content.

## iOS-specific

### Privacy manifest (`PrivacyInfo.xcprivacy`)
Required since May 2024: any use of an Apple-designated "Required Reason API" (examples: `UserDefaults`, file timestamp APIs, disk space APIs, active-keyboard-detection APIs) must be declared in a privacy manifest with an approved reason code, or the submission is rejected (error code `ITMS-91053`). This applies to third-party SDKs too - an SDK using one of these APIs without shipping its own manifest makes the rejection the app owner's problem, not the SDK vendor's. Audit dependencies for this before a first submission, since it's easy to miss when the API usage is buried inside a library rather than the app's own code.

### Sign in with Apple
If the app offers any third-party social login (Google, Facebook, etc.), Apple requires also offering "Sign in with Apple" as an equally prominent option. Plan this into the auth screen design from the start if any social login is planned at all, not after a rejection.

### Encryption export compliance
Every submission answers an export-compliance question about encryption usage (`ITSAppUsesNonExemptEncryption` in `app.json`/`Info.plist`). Standard HTTPS/TLS usage typically qualifies for an exemption, but this is a real legal declaration, not a formality to click through - know the actual answer for the app rather than guessing.

## Android-specific

### Target API level
Google enforces a minimum target SDK level on an annual cycle for new apps and updates - as of 2026, new apps must target API 36 (Android 16) by August 31, 2026. Check the current requirement at build time rather than assuming a previously-correct target level is still current; this requirement moves forward roughly yearly and blocks submission if missed.

### Closed testing requirement for new developer accounts
Any **personal** Google Play developer account created after November 13, 2023 must complete a closed test - **12 opted-in testers, active continuously for 14 consecutive days** - before production access is granted (reduced from 20 testers in December 2024). Key details:
- Testers must actually open/use the app throughout the window on real devices with genuine Google accounts - emulators, bots, or testers who install-then-go-inactive don't count, and Google's systems actively detect this.
- If the tester count drops below 12 at any point during the window, the 14-day clock resets.
- **Verified organization accounts** (registered with a legal business entity) are exempt from this requirement - only personal accounts are affected.
- Build this lead time into the release schedule from the start - 14 days minimum, realistically longer once you account for tester recruitment and any reset from a dropout. This is not something that can be rushed the week of a planned launch.

### Play App Signing
Enroll in Google Play App Signing (Google manages the app signing key; the developer holds only an upload key) rather than managing the full signing key manually - this is the current recommended default and protects against key loss being catastrophic.

## Pre-submission checklist (both platforms)
- [ ] Account deletion built and reachable in-app, plus a web path (Android)
- [ ] Privacy policy live, linked in-app and in store metadata, and matches actual data practices
- [ ] iOS App Privacy nutrition label / Android Data safety section completed and audited against every bundled SDK
- [ ] ATT prompt implemented if any cross-app tracking occurs (iOS)
- [ ] Support URL live, reachable with no login, with a real contact method
- [ ] Every requested permission has a specific (non-boilerplate) usage description string
- [ ] App icon, screenshots, and content rating current for the actual submitted build
- [ ] iOS: `PrivacyInfo.xcprivacy` manifest present and covers both first-party and third-party Required Reason API usage
- [ ] iOS: Sign in with Apple present if any other social login is offered
- [ ] iOS: encryption export compliance answer verified, not guessed
- [ ] Android: target API level matches the current year's Google requirement
- [ ] Android: closed testing (12 testers / 14 days) scheduled with enough lead time if this is a new personal developer account
- [ ] Android: Play App Signing enrolled
