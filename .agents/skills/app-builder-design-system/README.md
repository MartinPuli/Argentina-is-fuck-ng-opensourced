# App Builder Skills

---

## Principles

**Know who it's for.**
Everything else follows.

**Systems, not snowflakes.**
One token. Everywhere. Change it once, and the whole product moves with it.

**Every state is a promise.**
Loading. Empty. Error. Disabled. Done means all four - not the happy path alone.

**Both platforms. Every time.**
iOS and Android are peers. Neither is the default the other has to catch up to.

**Secure the data before you design the screen.**
The backend is the contract. The frontend is the conversation.

**If it moves, it means something.**
Motion is feedback, continuity, or delight. Never decoration for its own sake.

**Trust nothing the client sends.**
Protect everything the client can't see. Security that isn't invisible isn't finished.

**Nothing about launch day is a surprise.**
Shipping is a checklist. Not a hope.

**Make it work. Make it whole. Then make it unforgettable.**
Depth and delight are earned - in that order.

Every step here can be skipped, for now. Say so, and Claude moves on - noting what's deferred, not pretending it isn't needed. Structure, not a straitjacket.

---

## What's inside

```
app-builder/
├── SKILL.md ← start here
└── references/
 ├── design-tokens.md Color, type, spacing, radius token structure
 ├── components.md Full component catalog + required states
 ├── patterns-and-edge-cases.md Platform gotchas, forms, empty states, sharing
 ├── animation-and-motion.md Duration/easing/spring tokens + delight catalog
 ├── backend-patterns.md Supabase schema, RLS, RPC conventions
 ├── file-structure.md Where every file goes
 ├── advanced-practices.md Performance, lists, data-fetching, TypeScript
 ├── app-lifecycle-essentials.md Config, permissions, error handling
 ├── security-and-data-protection.md The client is never trusted
 ├── store-publishing-checklist.md Current App Store / Play Store requirements
 └── planning-template.md The plan doc format Claude produces per phase
```

## Install

**Claude.ai / Claude apps** - download `app-builder.skill` from [Releases](../../releases), upload it in **Settings → Capabilities → Skills**, and start describing your app.

**Claude Code** - clone this repo into your project's skills directory. Auto-discovered.

**Just reading** - every file under `references/` stands alone as a design-system reference, Claude or not.

Full detail in `SKILL.md` → **Install**.

## Start here

`SKILL.md` is the whole system - vision, process, and every rule Claude follows before it writes a line of code. Read it top to bottom once. After that, it's a reference you dip into.

## Contributing

This is meant to be forked, argued with, and improved. If a pattern here is wrong, out of date, or missing something you've been burned by - open an issue or a PR. The `references/` files are plain markdown; no build step required to edit them. If you change `SKILL.md`'s frontmatter `description`, keep it under 1024 characters (Claude Skills' hard limit).

## License

MIT - use this however helps you ship better software.
