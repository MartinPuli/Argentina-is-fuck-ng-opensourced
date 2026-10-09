# Patterns & Edge Cases

Cross-cutting issues that are easy to miss in any React Native / Expo build. Apply these proactively - don't wait for a bug report.

## Safe area handling
- Root `SafeAreaProvider` MUST be given `initialMetrics={initialWindowMetrics}` (from `react-native-safe-area-context`). Without it, Android's first render has no inset data and top content gets cropped under the status bar.
- **Never nest two `SafeAreaView`s** in a parent→child screen relationship (e.g. a detail screen rendered inside a wrapper screen that's also a `SafeAreaView`). The inset is not automatically "consumed" - both apply the full top inset, doubling the gap. Fix pattern: give the inner/reusable screen component a `noTopInset` prop that swaps `SafeAreaView edges={['top']}` for a plain `View` when it's being embedded, and have the parent screen own the single top inset.
- Prefer a shared `SafeScreen` wrapper component (`flex:1`, themed background, `edges` prop, `noTopEdge`/`noBottomEdge` shorthand) over importing `SafeAreaView` ad hoc in every screen - keeps the whole app consistent and makes a future safe-area fix a one-file change instead of a many-file find-replace.

## Platform-specific share
`Share.share({ url })` - **the `url` field is silently ignored on Android.** Always branch:
```js
if (Platform.OS === 'android') {
 await Share.share({ message: `${text}: ${url}`, title });
} else {
 await Share.share({ message: text, url, title }); // iOS honors url separately
}
```
A share button that "seems to work" on iOS but sends text-only on Android is one of the most common regressions in RN apps - test both platforms for every share flow.

## Login / auth flow order of operations
Avoid pre-checking "does this email exist" via a separate query/RPC before attempting sign-in - a user can exist in the auth system without a completed profile row, making an existence-check-by-profile-table return a false negative and block a valid login before the password is even tried. Correct order:
1. Attempt sign-in directly.
2. On an "invalid credentials" error (most auth providers return the same generic error for both wrong email AND wrong password) - **then** check email existence separately to decide which message to show (Account Not Found vs Incorrect Password).
3. Handle "email not confirmed" as its own branch, routed to verification.
4. Always reset any in-flight "logging in" ref/flag on every early-return path, not just in a final `finally`.

## Multi-image picker (a common Android bug)
When using an image picker library with multi-select enabled, calling an add/append function once per selected asset (looped) can result in only the last image surviving on Android due to interleaved state updates. Fix: collect all picked URIs first, then make **one single state update** that adds all of them (deduplicated against existing items) at once.
```js
const newUris = result.assets.map(a => a.uri).filter(Boolean);
setItems(prev => {
 const existing = new Set(prev.map(p => p.localUri).filter(Boolean));
 const toAdd = newUris.filter(uri => !existing.has(uri)).map(uri => ({ id: makeId(), localUri: uri,... }));
 return [...prev,...toAdd];
});
```
Also: image-editing/cropping is often incompatible with multi-select on Android (only crops/returns the last asset) - disable edit mode for the multi-select path and offer single-pick-with-crop as a separate flow.

## Responsive type & spacing
See `design-tokens.md` for the scale formula. Rule of thumb: **design against the largest device you test on**, and every other device scales *down* from there, never up. Android typically needs an additional reduction on top of the width ratio because Android font rendering tends to look visually heavier at the same point size.

## Empty-state image gating
```js
const EMPTY_IMAGE = require('../assets/EmptyState.png');
Image.prefetch(Image.resolveAssetSource(EMPTY_IMAGE).uri).catch(() => {}); // module-level, once

// in component:
const [imageReady, setImageReady] = useState(false);
<Image source={EMPTY_IMAGE} onLoad={() => setImageReady(true)} onError={() => setImageReady(true)} />
<View style={[styles.textBlock, !imageReady && styles.hidden]}> {/* title/subtitle */} </View>
```
This prevents the flash where text renders instantly but the illustration pops in a beat later.

## Count/badge animation
A worked example of the `bouncy` spring preset from `animation-and-motion.md`, applied to a count badge. Bounce a count badge (not just fade) using a small spring sequence keyed off the count *changing*, not just its value:
```js
useEffect(() => {
 const prev = prevCountRef.current;
 if (count === prev) return;
 if (prev === 0 && count > 0) { /* pop in: bouncy preset, spring to 1 */ }
 else if (count === 0) { /* gentle preset, spring to 0, then clear displayed number */ }
 else { /* bounce: bouncy preset, spring to ~1.45 then settle to 1 with gentle */ }
}, [count]);
```
Keep the badge `View` mounted (don't conditionally unmount at count 0) so the scale-out animation has something to animate.

## Swipe/accept-reject card interaction pattern
A worked example of asymmetric enter/exit and the delight-moments catalog from `animation-and-motion.md`. Positive action: `bouncy` preset spring bounce on the confirming button/icon (scale 0.88 → 1.07 → 1) plus an icon burst - celebratory, fast, per the Delight Moments catalog. Negative/dismiss action: `deliberate` duration token, `standard` easing - the item slides out horizontally and fades, *then* the underlying state update fires (don't update state mid-animation), then any resulting placeholder/undo row springs in (`gentle` preset) from a hidden state. The dismiss path should read as unmistakably faster and less ceremonious than the accept path - see the asymmetric enter/exit rule.

## Nested-list "isLast" border logic
When a card renders a series of conditionally-present rows, each row's `isLast` prop must check that **every subsequent conditional field is also falsy**, not just compare against a static array length. Getting this wrong leaves a trailing border under what's visually the last row.

## Form validation patterns
- Digits-only fields: strip non-digits on every keystroke, validate exact length only on submit/blur (avoid error-flashing while the user is still typing).
- Multi-item forms with an add/remove list where exactly one item must be "primary": recompute a single-primary invariant via a pure helper function after every add/remove/toggle, rather than trusting incremental state mutations to stay consistent.
- "Leave without saving" guard: use the navigator's `beforeRemove`-style listener, prevent the default navigation, and show a 3-way choice (Save / Discard / Continue Editing) - a bare native "are you sure" alert isn't enough for anything with more than one field.

## Haptics
Use `expo-haptics` (wraps iOS's Taptic Engine and Android's vibration motor behind one API) consistently rather than triggering vibration ad hoc per component. Every interactive component that supports haptics (see `Button` in components.md) should accept a `haptic` prop (`'none' | 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection'`) rather than each screen calling the haptics API directly - this keeps the mapping from interaction type to haptic feel consistent app-wide and makes a later global adjustment a one-file change.

### Mapping interaction → haptic type
- **`selectionAsync()`** - moving between discrete options where no state has been committed yet (scrolling a picker wheel, dragging across a segmented control, swiping between carousel pages). Selection haptics are the lightest and most repeatable - safe to fire on every step change.
- **`impactAsync(Light)`** - a low-stakes tap: toggling a checkbox, switching a tab, pressing a secondary/outline button.
- **`impactAsync(Medium)`** - a primary, committing action: submitting a form, confirming a primary button, accepting/connecting.
- **`impactAsync(Heavy)`** - a rare, high-weight action: a destructive confirm (delete account), a significant milestone completing.
- **`notificationAsync(Success)`** - an async operation completed successfully (save succeeded, upload finished, payment confirmed).
- **`notificationAsync(Warning)`** - a recoverable problem the user should notice but isn't blocked by (a soft validation warning, a "you're about to lose progress" moment).
- **`notificationAsync(Error)`** - an operation failed (save failed, network error, invalid submission).

### Rules
- **Never fire a haptic on every scroll/frame tick.** Selection haptics on a picker are fine per discrete step change, but a haptic firing on every pixel of scroll movement causes haptic fatigue and feels broken, not premium.
- **Haptics accompany a state change, not a render.** Firing a haptic in a `useEffect` keyed to something that re-renders without the user having done anything (e.g. a prop updating from a background refetch) will surprise the user with unexplained buzzing - only fire from a direct response to user input or a definitive async result (success/error).
- **Respect the OS-level setting.** If a user has disabled system haptics/vibration, `expo-haptics` calls should silently no-op rather than the app trying to force vibration through a different API - never bypass the user's device-level preference.
- **Don't block the interaction on the haptics call.** Fire-and-forget - `Haptics.impactAsync(...)` is async but nothing in the UI should wait on it resolving.
- **Platform asymmetry is expected and fine.** iOS haptics (Taptic Engine) are richer and more distinct between impact weights than Android's vibration motor equivalent - don't chase pixel-perfect haptic parity between platforms; the *category* of feedback (light vs. success vs. error) matching is what matters, not that they feel identical.
- **Pair a haptic with a visual change, never send haptic feedback alone.** A haptic with no accompanying visual state change (a color shift, an icon change, a snackbar) reads as a glitch - haptics are a reinforcement channel, not a standalone signal.
- **Destructive/heavy haptics need deliberate restraint.** Reserve `Heavy` impact and any single Warning/Error haptic for moments that are genuinely rare in a session - overusing strong haptics numbs their signal value exactly like overusing a modal or a red error color would.


## Text scaling & wrap safety
Any button label or badge that could wrap to 2 lines on a small device is a bug, not a design nuance - either reduce horizontal padding responsively or shorten the copy for the given width bucket. Test the narrowest supported Android width (commonly ~360px) explicitly for every new button/label.
