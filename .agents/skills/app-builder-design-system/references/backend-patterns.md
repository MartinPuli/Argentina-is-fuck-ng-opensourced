# Backend Patterns (Supabase)

General conventions for structuring a Supabase backend for a mobile app. Apply this shape to any new app - specific table names and domain logic change, the *pattern* doesn't.

## Sequencing - always backend first
1. Define tables + columns
2. Define RLS policies (never ship a table without RLS enabled from the first migration)
3. Define RPCs for anything that needs to bypass/combine RLS-safe logic (existence checks, mutual-relationship checks, computed routing logic)
4. Define storage buckets + signed URL strategy for any user-uploaded media
5. Only then write the hook (`use<Thing>.js`) that calls into 1-4
6. Only then write the screen that calls the hook

## Table naming & core-identity pattern
Split identity into a lightweight, frequently-joined "core" table (id, slug/handle, published/visible flag, a few commonly-needed fields) versus heavier or privacy-sensitive data in separate tables that hang off the core table's id via foreign key. Don't widen a core identity table indefinitely - anything optional, large, or access-restricted gets its own table.

## RLS - mutual/bidirectional relationship checks
When two users need mutual-consent visibility of each other's data (e.g. contact info only visible once both sides have opted in), express the check as an `.or()` filter covering both directions rather than writing two separate one-way policies:
```sql
-- conceptually, in an RPC or RLS policy:
(actor_id = auth.uid() AND target_id = other_user_id AND status = 'accepted')
OR
(actor_id = other_user_id AND target_id = auth.uid() AND status = 'accepted')
```
Compute this once as a single boolean (e.g. `canViewDetails`) and reuse it for every gated field in that response - don't re-derive it per field.

## RPC conventions
Use a Postgres RPC (not a raw table query from the client) whenever the check:
- needs to run as a privileged check across tables the client shouldn't directly query (e.g. checking auth-system tables the client has no direct SELECT access to)
- needs to compute routing/decision logic server-side (e.g. "what screen should this user see next") - keeps that logic in one place instead of duplicated across client screens
- combines multiple tables/conditions into a single boolean or value the client can trust without re-deriving it

Name RPCs consistently (pick either verb_noun or noun_verb and stick to it for the whole project).

**Known trap:** an "email/account exists" RPC that queries a *profile* table (rather than the underlying auth table) will return false negatives for users who signed up but never completed onboarding/profile creation. Decide explicitly which table existence-check RPCs query, and document it - this exact category of bug is a common cause of "valid user can't log in" reports.

## Storage & signed URLs
- User-uploaded media goes to a dedicated bucket, not a public bucket by default, unless the content is genuinely meant to be publicly accessible without auth.
- Client-side, resolve display URLs via a signed-URL call with a reasonable expiry (long enough to cover a typical session), re-resolving on next load rather than caching indefinitely.
- Store the **object path**, not the signed URL, in the database row - signed URLs expire, paths don't.
- Client upload flow: store the local URI optimistically in local state immediately (so the UI shows the new content before upload completes), upload in the background, then swap to the persisted object path once the upload confirms. Don't block navigation on upload completion for non-critical flows - let it complete in the background and retry on the next save-critical action if needed.

## Migration discipline
- Every schema change is a migration file, never a manual dashboard edit for anything beyond local prototyping.
- RLS policy changes ship in the same migration as the table/column change they gate, not as an afterthought migration.

## When to reach for Supabase MCP tools
If Supabase MCP tools are available in this session, use them for:
- listing tables/migrations before assuming a schema - never guess at existing structure, look it up
- applying migrations for schema changes rather than hand-writing SQL the user has to run manually, when there's an active connected project
- running the advisors check after any schema change to catch missing RLS or security issues immediately, not after the fact
