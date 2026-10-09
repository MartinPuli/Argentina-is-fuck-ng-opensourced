# Animation & Motion System

This is the missing piece that was previously scattered - a badge-bounce spec here, an accept/reject choreography there, a "use Reanimated" line in advanced-practices - with no shared vocabulary connecting them. This file is that shared vocabulary: duration tokens, easing/spring tokens, choreography rules, and a catalog of the specific moments in a typical app that deserve deliberate motion design. Every animation anywhere in the app should be describable as "duration token X, easing/spring token Y, for reason Z" - if it can't be, that's a sign the animation wasn't deliberately designed.

Grounded in Apple's WWDC motion guidance (spring-first, interruptible, velocity-aware) and Emil Kowalski's UI animation practice (duration discipline, purpose-first decisions), translated to React Native's Animated/Reanimated APIs.

## Step 0: should this even animate?
Before choosing a duration or easing, answer this - it's the most commonly skipped step:

| How often does the user see this? | Decision |
|---|---|
| Many times per session (list scroll, switching between already-visited tabs, keyboard-driven repeated actions) | No animation, or the absolute minimum - animation on a high-frequency interaction reads as latency, not polish |
| Occasional (opening a modal, submitting a form, a screen transition) | Standard animation from the tokens below |
| Rare / first-time / milestone (onboarding complete, first successful action, an achievement) | This is where delight animation belongs - see the Delight Moments catalog |

If the honest answer to "why does this animate?" is only "it looks nice" **and** the user will see it often, don't animate it. Purpose comes first; every animation should trace back to one of: feedback (confirming the app heard the input), spatial consistency (something enters/exits the way it visually came from/goes to), state indication (a value or status genuinely changed), or delight (a rare, earned moment).

## Duration tokens
Named scale, not ad hoc numbers per component. Pick the token, don't invent a new millisecond value per screen.

| Token | Duration | Use |
|---|---|---|
| `instant` | 100-120ms | Button press feedback, toggle flip - the interaction must feel simultaneous with the touch |
| `fast` | 150-200ms | Tooltips, small popovers, tab underline slide, chip selection |
| `base` | 200-280ms | Dropdowns, standard screen-local transitions, snackbar enter |
| `deliberate` | 300-450ms | Modal/sheet present, full-screen transitions, card accept/reject exit |
| `celebratory` | 500-900ms, often as a sequence of several steps | Rare, earned delight moments only - see catalog below |

**Rule of thumb: stay under 300ms for anything that isn't a rare celebratory moment.** A 180ms transition consistently *feels* more responsive than a 400ms one even when both are objectively "fast enough" - perceived speed is driven by duration and easing shape at least as much as by actual load/processing time.

**Asymmetric enter/exit:** exits should generally be faster than entries - the system responding to a dismissal should feel immediate, while an entry can afford a touch more presence. A modal that takes 350ms to appear but only 200ms to dismiss feels right; the reverse feels sluggish to leave.

## Easing & spring tokens

### Curve-based (non-interruptible motion - value changes with no gesture behind them)
Use React Native's `Easing` module with a custom bezier rather than the built-in linear/ease defaults, which are too weak to feel intentional:
```js
import { Easing } from 'react-native';

const EasingTokens = {
 standard: Easing.bezier(0.23, 1, 0.32, 1), // strong ease-out - default for anything entering/appearing
 moveOnScreen: Easing.bezier(0.77, 0, 0.175, 1), // ease-in-out - for something already visible repositioning
 linear: Easing.linear, // only for constant-rate motion: progress bars, marquees
};
```
- **Entering or exiting → `standard` (ease-out).** Starts fast, which is what makes it feel responsive - the user is watching most closely at the start of the motion.
- **Never use ease-in for a UI-initiated animation.** It delays the initial movement at exactly the moment being watched, which reads as sluggish regardless of total duration.
- **Repositioning something already on screen → `moveOnScreen` (ease-in-out).**
- **Constant-rate indicators (progress bars, marquees) → `linear`.**

### Spring-based (default for anything the user can touch, drag, or that carries momentum)
Springs are preferred over duration+easing for **any gesture-driven or interruptible** motion, because a spring re-targets smoothly from wherever it currently is - a duration-based animation restarts or jumps if interrupted mid-flight. Named presets (React Native `Animated.spring` stiffness/damping, or Reanimated `withSpring`):

| Preset | stiffness | damping | mass | Use |
|---|---|---|---|---|
| `gentle` | 260 | 26 | 1 | Default for anything settling into place with no bounce - a toggle, a focus-state shift, most UI that just needs to feel alive without overshoot |
| `snappy` | 400-500 | 28-32 | 1 | Quick, confident settle - button press release, tab focus change |
| `bouncy` | 500-600 | 8-14 | 1 | **Only** for momentum-driven or celebratory motion - something the user flicked/dragged and released, or a rare success/delight moment. Overshoot on a menu that just faded in feels wrong; overshoot on something that had momentum behind it feels right. |

This maps to Apple's damping-ratio/response mental model: `gentle` and `snappy` are close to critically damped (no bounce, graceful settle); `bouncy` is intentionally under-damped. **Default to `gentle` everywhere; reserve `bouncy` for the small set of moments in the Delight catalog below** - overusing bounce makes every interaction feel equally "exciting," which cancels out the effect entirely.

## Interruptibility - the single most important choreography rule
Any animation the user can interact with mid-motion (a drag, a swipe-to-dismiss, a card stack, a bottom sheet) must:
- **Never lock out input while it's animating.** A user grabbing a still-settling sheet should be able to redirect it immediately.
- **Animate from the current on-screen (presentation) value, not the original target**, when a new gesture interrupts an in-flight animation - restarting from the logical/target value causes a visible jump. Reanimated's shared values naturally support this if the gesture handler reads the live value rather than a stored target.
- **Use springs, not fixed-duration timing animations, for anything gesture-driven** - a `withTiming` or `Animated.timing` animation can't be smoothly re-targeted mid-flight the way a spring can.
- **Respond on touch-down, not touch-up.** Highlight/scale-down feedback on a button should fire on `onPressIn`, not wait for the full press-release cycle to complete - waiting for `onPress` to show any feedback reads as latency even if the actual handler runs instantly after.

## Multimodal feedback - motion, haptics, and sound in harmony
When a moment combines a visual change with a haptic (see patterns-and-edge-cases.md → Haptics) and/or a sound:
- **They fire on the same frame.** A haptic that lands 100ms after the visual change it's reinforcing breaks the illusion that they're one event - trigger both from the same callback, not from two independently-timed effects.
- **Character should match.** A light tap gets a light haptic and a subtle visual nudge; a heavy, rare celebratory moment can pair a stronger haptic with a bigger, `bouncy`-preset visual moment. Mismatched intensity (a huge visual celebration with no haptic, or a heavy haptic on a tiny UI change) feels off even when neither element alone is wrong.
- **Reserve multi-sense feedback for moments that earn it** - success, error, a meaningful commit, a snap-into-place. Firing haptics+sound+animation together on routine, frequent actions trains the user to tune out all three.

## Choreography for groups of elements
- **Stagger, don't simultaneous-pop, when multiple items enter together** (a list populating, a grid of cards appearing). Delay each subsequent item by roughly 30-80ms from the previous one - long enough to read as a cascade, short enough that it doesn't feel slow. Stagger is decorative: never block interaction while stagger is still playing on later items.
- **One state change animates at a time per component, unless explicitly choreographed as a sequence.** A card that's simultaneously changing opacity, position, AND its internal content is a common source of janky-feeling motion - sequence or explicitly coordinate multi-property changes rather than letting them fire independently and hope they land in sync.
- **Exit before enter, when replacing one element with another in the same screen position** (e.g. an error state replacing a loading state) - a brief overlap or a coordinated cross-fade reads as intentional; two elements racing to their end states independently reads as glitchy.

## Reduced motion
- Check the OS-level "reduce motion" accessibility setting (`AccessibilityInfo.isReduceMotionEnabled()`, or Reanimated's reduced-motion utilities) and branch: replace slide/spring/parallax motion with a short opacity cross-fade instead, drop overshoot/bounce entirely, but **keep** opacity and color transitions that aid comprehension - reduced motion means gentler, not zero feedback.
- This is a per-user preference, distinct from the responsive size/spacing scaling in design-tokens.md - one adapts to device size, the other adapts to a stated accessibility need, and both need to be handled, independently.

## Delight Moments catalog
This is the concrete list to check against Phase 3 ("depth & delight") of the planning workflow - these are the moments in a typical app that are worth deliberately over-investing in, because they're rare enough per user that the extra polish reads as delight rather than friction:

| Moment | Treatment |
|---|---|
| First successful core action (first booking, first match, first item added - whatever the app's central task is) | `bouncy` preset + matching haptic (`notificationAsync(Success)`) - this is the single highest-leverage delight moment in most apps and is worth the most design attention |
| Onboarding completion | A short celebratory sequence (not just a plain screen transition) - this is the last impression before the user reaches the "real" app |
| Accept/like/connect-style positive action | Spring bounce on the confirming element (scale ~0.88 → 1.07 → 1, `bouncy` preset) + an icon burst - see the worked example in patterns-and-edge-cases.md |
| Decline/reject/dismiss action | Faster than the positive path - slide out + fade (`deliberate` token, `standard` easing), state update fires only after the exit completes, not mid-animation |
| A count/badge changing | Bounce keyed to the change, not the value - see the worked example in patterns-and-edge-cases.md |
| Empty → populated transition (first item appears in a previously-empty list) | Worth a slightly more generous entrance than routine subsequent items - this is the moment the empty state's promise gets fulfilled |
| Pull-to-refresh completing with new content | A brief, light confirmation (not a full celebratory sequence - this repeats often, so keep it in `fast`/`base` territory per the frequency rule above) |
| Milestone / streak / achievement (if the app has these) | Reserve the `celebratory` duration token and `bouncy` preset for these specifically - this is exactly the "rare and earned" category the whole duration scale is built around |
| Error / validation failure | A short, restrained shake or color-flash (`fast` token) + `notificationAsync(Error)` haptic - errors need to register clearly but should not be visually loud, since they're often the user's fault-free discovery of a real problem and shouldn't feel punitive |

The common thread: **the rarer and more meaningful the moment, the more the motion is allowed to depart from the restrained default** - and the more frequent an interaction, the more the motion should recede toward "the absolute minimum needed for it not to feel broken."

## Anti-patterns to avoid
- Animating on every scroll frame or every keystroke - see Haptics' equivalent rule; the same restraint applies to visual motion.
- The same animation treatment for a routine action and a rare one - if the "success" animation for saving a routine form field looks identical to the "you completed onboarding" animation, neither one lands as special.
- Blocking user input until a decorative animation finishes - a stagger, a page transition, or a celebratory sequence should never be the thing standing between the user and their next tap.
- Reusing `Animated.timing` for anything gesture-driven - this is the single most common "why does this feel slightly off" bug in RN apps with drag/swipe interactions; if a gesture can touch it, it should be spring-driven.
