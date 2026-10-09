# Component Catalog & Required States

Every component below must be designed/implemented with ALL listed states - a component that only handles the happy path is incomplete. This catalog reflects the actual set of standard components a mature app in this style accumulates. When a new app request touches any of these, assume the component should exist and follow these rules rather than inventing a one-off pattern.

Import all of these through a single `components/index.js` barrel so screens do `import { Button, Input, Modal } from '../components'` rather than deep-importing each file.

---

## Foundational inputs & actions

### Button
Variants: `primary` (filled, brand color), `secondary` (filled, muted), `outline` (border only), `ghost` (no border/fill - icon-only, tab-bar style).
Required states: default, **disabled** (reduced opacity, blocks `onPress`), **loading** (spinner replaces/joins label, implicitly disables press), **pressed** (`snappy` spring preset scale-down, fired on touch-down not touch-up - see animation-and-motion.md's Response/Interruptibility rules; never an instant snap or a delayed touch-up-only feedback).
Every Button accepts a `haptic` prop (`'none' | 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection'`, default `'light'` for most variants) rather than screens calling the haptics API directly - see patterns-and-edge-cases.md → Haptics for the full interaction-to-haptic-type mapping and rules.
Icon-only ghost buttons need `hitSlop` and a fixed ≥40×40 touch target even if the icon itself is smaller.

### Input
Required states: default, **focused**, **error** (inline helper text in danger color, border shifts to match), **disabled**.
Props: `label`, `placeholder`, `secureTextEntry`, `keyboardType`, `nextFieldRef` (return-key chaining), `onSubmitEditing`, `returnKeyType`.
Digits-only fields strip non-numeric characters on every keystroke; validate exact length only on blur/submit, not per-keystroke.

### Radio (button group)
A labeled set of mutually-exclusive options. Required states: default, selected, disabled (whole group or per-option). Always renders as a real list (not a dropdown) when the option count is small (≤5) and a `Modal`-style picker when the list is long - don't default to a long scrollable radio list for a 20-item enum.

### CheckboxRow
Single labeled toggle row (not a bare checkbox - always paired with a tappable label). States: unchecked, checked, disabled. The entire row is the tap target, not just the checkbox glyph.

### Chips (filter/selection chips)
Distinct from `Tags` (below) - Chips are **interactive selection controls** (e.g. filter toggles), Tags are **display-only** labels. Chips need selected/unselected visual states and should support multi-select or single-select mode explicitly via a prop, not by convention.

### Tags
Read-only label pills, `chip` vs `chipSelected` type tokens even though nothing is tappable (selected state can still indicate "your tag" vs "others'"). Wrap in `flexWrap: 'wrap'` with consistent `gap`; avoid a horizontal ScrollView unless the design explicitly calls for a single-row scroller.

### CustomSlider
Range or single-value slider. Required states: default, dragging (visually distinct thumb/track), disabled, and a **labeled value display** that updates live during drag - never a slider with no numeric readout for anything other than a purely aesthetic control.

---

## Pickers

### BirthdayPicker / YearPicker / HeightPicker
Specialized single-purpose pickers - don't build a generic "picker" and configure it three ways; each of these encodes domain-specific constraints (birthday needs a sane year range and leap-year-aware day counts, height needs a sensible unit range). Required states: default/empty (no value selected yet - must be visually distinct from a real default value, e.g. don't default a height picker to a specific height silently), selected, disabled.
General picker rule: **never let a picker component itself decide what happens to invalid/out-of-range state** - an empty value is a valid, distinct state the parent form must handle (see components.md → Input error state pattern).

### MultiSelectModal
Multi-select variant of the picker/confirmation `Modal` - same visual shell, different selection semantics (array value instead of single value, a visible count of selections, a clear-all affordance). Needs its own component rather than overloading `Modal` with a `multiple` prop once the selected-count UI and confirm/apply button differ meaningfully from the single-select flow.

---

## Modal / sheet family

### Modal (confirmation / selection style)
Two roles, same component: a **selection picker** (options list) and a **confirmation dialog** (named actions, not generic OK/Cancel). Props: `label`/`title`, `subtitle`, `options`, `value`, `onValueChange`, `onClose`, `required`, `error`.
`onClose` is always wired - tapping the scrim or the system back button is an explicit "cancel"/"stay" choice, never a silent no-op.

### PremiumUpsellModal
A distinct modal type from generic confirmation - paywall/upsell surfaces need their own component because they carry different obligations: a visible, unambiguous dismiss action (never trap the user), no dark patterns (don't disable the close button or delay its appearance to force viewing), and a clear list of what's being unlocked. Treat "can the user always leave for free" as a hard requirement, not a nice-to-have.

---

## Feedback & loading

### Snackbar / Toast
`variant`: `success` | `info` | `error`. Props: `visible`, `message`, `variant`, `onDismiss`. Keep auto-dismiss timing consistent app-wide.

### LoadingScreen
Full-screen loading state (not a component-level spinner) for screen-level async waits - e.g. initial data fetch before anything else can render. Should never appear for more than a few seconds without a fallback/error path; pair every `LoadingScreen` usage with a corresponding error state the caller handles explicitly.

### SkeletonLoader
Content-shaped shimmer placeholder used **instead of** `LoadingScreen` whenever the final layout is already known (a list of cards, a profile header) - skeletons reduce perceived wait time more than a spinner because the eye can anticipate the coming layout. Rule of thumb: if you know the shape of what's loading, skeleton it; if you don't (e.g. a totally unknown-length initial fetch), use `LoadingScreen`.

### Badge
Small numeric/status indicator, distinct from a `Tag`. Required states: **zero** (hidden or explicit empty variant, never a bare "0"), **populated**, **overflow** (capped display, e.g. `99+`). See patterns-and-edge-cases.md for the bounce animation spec when the count changes.

---

## Structural / layout

### Footer
Two variants: `single` (one full-width primary action) and `dual` (secondary/back + primary continue, typically `flex: 1` / `flex: 2`). Exports a `FOOTER_HEIGHT` constant - every scrollable screen with a persistent footer MUST add `FOOTER_HEIGHT + <spacing>` to its scroll content's bottom padding.

### Card / CardStack
`card.js` - a single content card (the visual unit). `CardStack.js` - a swipeable/stacked deck of cards (e.g. a browse/discover-style interaction) built ON TOP of `card.js`, not a reimplementation. Required states for the stack: empty (no more cards - always has a defined empty state, see Empty states below), loading next batch, single-card (last card, no card visible behind it - the stack's shadow/depth effect must degrade gracefully to a flat single card here).

### FormCard
Plain bordered form-section card, typically paired with `SectionTitle` above it.

### SectionTitle
Section header text component distinct from the `sectionHeader` type token - this is the *component* wrapping that token, and should support an optional trailing action (e.g. "See all") without every screen re-implementing that row layout.

### SectionTabs
Segmented control / in-screen tab switcher (distinct from the app's root `TabBar`) - used to switch between views within a single screen (e.g. "Details" / "Reviews" / "Photos" on one profile). Required states: default, selected, and a visible active-indicator that animates between positions rather than snapping.

### Carousal / Carousel
Horizontal paged image/content carousel. Required: page indicator dots, graceful 1-item state (no indicator dots needed for a single item), and a defined placeholder for the zero-items case (never render an empty carousel with just blank space).

### ProfileActionBar
A **persistent, screen-specific** bottom action bar - distinct from the generic `Footer` component because it's typically anchored to one particular screen's primary entity (e.g. actions tied to whatever profile/record is currently being viewed) and often needs to coordinate with the root tab bar's height/visibility rather than being a simple screen-local footer. If a new app has an equivalent "actions tied to the thing you're looking at" pattern, model it as its own component rather than overloading `Footer`.

### TabBar
Custom bottom tab bar (if the app needs one beyond the navigator default) - platform-aware background treatment (blur/glass on iOS, solid on Android/web), badge support (via `Badge`), and press animations. See patterns-and-edge-cases.md for the safe-area and shadow considerations.

### PublicViewerNavbar
A navbar variant shown only in unauthenticated/public viewing contexts (e.g. viewing a shared link without an account) - kept distinct from the authenticated app's normal navigation chrome so public pages can't accidentally expose authenticated-only actions.

---

## Onboarding / splash

### AnimatedSplash
A custom animated launch/splash sequence beyond the static Expo splash screen. Must have a hard maximum duration and always resolve to the next screen even if an animation asset fails to load - never let a splash animation become a dead end if the asset fetch/decode fails.

### Stepper
`currentStep` / `totalSteps` progress indicator for multi-step flows - every step screen must pass both explicitly; a missing `totalSteps` silently breaks the progress math.

### UploadPhoto
The "add a photo" affordance used inside photo-grid screens - see patterns-and-edge-cases.md for the multi-select Android batching fix and the fixed-height-cell grid pattern this component's containers must follow.

---

## Empty states
Every empty state (list, carousel, card stack, discover feed, etc.) needs:
1. An illustration image, **prefetched at module load** (`Image.prefetch(...)` outside the component)
2. Image rendered with `onLoad`/`onError` gating title/subtitle behind an `imageReady` flag
3. A title + subtitle
4. A recoverable action where one exists (retry, adjust filters) - don't leave a dead end if there's something the user could do

## Accessibility baseline (apply to every component above)
- `accessibilityRole` set on every pressable custom component
- Minimum 40×40 touch target for icon-only buttons, padded via `hitSlop` if the icon itself is smaller
- Any image conveying information (not pure decoration) needs an accessible label if the platform default isn't sufficient
