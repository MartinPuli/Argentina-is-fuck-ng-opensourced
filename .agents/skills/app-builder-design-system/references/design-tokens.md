# Design Tokens

This describes the *shape* of a token system, not one fixed set of values. When starting a new app, propose or ask for the actual brand values (colors, font family, base sizes) and fill this structure in - never assume a prior project's specific palette or fonts carry over.

## Typography

### Font families
A small, deliberate weight set (commonly 3: a bold, a medium/demi, and a regular) rather than a large uncontrolled range. Example shape:
```js
FontFamilies = {
 bold: '<Brand>-Bold',
 demi: '<Brand>-Demi', // or semibold/medium depending on the family
 medium: '<Brand>-Medium', // or regular
}
```
Keep the weight count small and intentional - adding a 4th or 5th weight should be a deliberate design decision, not an accumulation of one-off overrides.

### Base sizes
Pick a **design baseline device** - typically the largest/most common target device - and tune all base font sizes against that. Common scale (adjust per brand):
```js
FontSizes = { 40, 28, 24, 20, 18, 17, 16, 15, 14, 12 }
LineHeights = { 52, 32, 30, 28, 24, 23, 22, 16 }
```

### Responsive scaling - MANDATORY for every new app
Never ship flat, unscaled font sizes across devices - text that looks right on the design baseline device will look oversized on a smaller or a differently-rendering platform. Pattern:

```js
const DESIGN_WIDTH = <baseline device logical width>;
const ANDROID_BASE = 0.92; // Android renders heavier + most Android devices are narrower than the iOS baseline
const FONT_SCALE_WEB = 0.9;

const FONT_SCALE = (() => {
 if (Platform.OS === 'web') return FONT_SCALE_WEB;
 const screenRatio = Math.min(1, SCREEN_WIDTH / DESIGN_WIDTH); // never scale UP on larger screens
 return Platform.OS === 'android'
 ? Math.max(0.82, screenRatio * ANDROID_BASE)
 : Math.max(0.82, screenRatio);
})();
```
Apply the same pattern for a `SPACE_SCALE` (a slightly higher floor, e.g. 0.88, so layouts don't visually collapse) with a `scaleSpace(value)` export for one-off responsive values used outside the type tokens.

### Type token catalog (shape, not values)
Organize semantic type styles by *role*, not by raw size - every screen pulls from named roles, never a raw `fontSize:` in a screen's `StyleSheet`. Typical roles to cover:

| Token | Use |
|---|---|
| `pageTitle` | Screen H1 |
| `sectionHeader` | Card/section headers |
| `cardTitle` | Card titles |
| `modalTitle` | Modal headers |
| `subtitle` | Screen subhead |
| `bodyPrimary` / `bodySecondary` / `bodyTertiary` | Body copy at decreasing emphasis |
| `primaryValue` | Emphasized inline value |
| `label` / `formLabel` | Field/section labels |
| `hint` | Helper text under inputs |
| `badgeLabel` | Tiny uppercase badge text |
| `empty` | Empty-state text |
| `caption` / `captionBold` | Smallest body text, two weights |
| `button` | Button label |
| `chip` / `chipSelected` | Tag/chip text, unselected vs selected |
| `option` / `optionSelected` | List option row text, unselected vs selected |
| `snackbar` | Snackbar/toast message text |

## Color system
Organize by semantic role, not raw hex - every screen references a category + role (e.g. `Colors.text.primary`), never a raw hex inline. Typical category shape:
```js
Colors = {
 text: { primary, secondary, tertiary, muted, label, hint, onLight, onDark },
 brand: { primary, onPrimary },
 surface: { page, card, subtle, soft },
 border: { subtle },
 status: { danger, success, warning? },
 icon: { muted, primary },
 overlay: { scrim },
}
```
When starting a new app: keep this category shape, fill in new hex values per brand. Never flatten the structure to inline hex codes in components.

## Spacing scale
A keyed spacing object (`Space[n]`) rather than raw numbers scattered through styles. A loose-but-token-based scale (not necessarily a strict 4px/8px grid at every step) is fine - the point is that every spacing value in the app traces back to one named scale, so a global spacing adjustment is a one-file change.

## Radius scale
Small numeric radii used directly for cards/buttons, plus a semantic "extra-large" token for sheet/tab-bar corners. Circular elements compute `borderRadius` from `width / 2`.

## Shadow / elevation - platform-split, always
Never a single cross-platform `shadow*` block. Always:
```js
...Platform.select({
 ios: { shadowColor: '#000', shadowOffset: { width: 0, height: -4 }, shadowOpacity: 0.04, shadowRadius: 16 },
 android: { elevation: <n> },
 web: { boxShadow: '0 -4px 24px rgba(16,24,40,0.06)' },
})
```
Tune opacity/elevation per component weight, but always provide all three platform branches - a component missing the Android `elevation` branch will render flat on Android even if iOS looks correct.
