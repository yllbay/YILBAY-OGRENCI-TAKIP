# Production Question Pool Contract

The human user's latest requirement takes precedence over old handoff prompts:
existing Question Studio folders, questions, and question assets must never be
deleted, renamed, rewritten, seeded, or replaced during development or deployment.
New folders/questions may be added through the real application's explicit UI/API.
Do not create or delete test questions in production. Use disposable databases,
object stores, and containers for acceptance checks.

## Required invariants

- Branch `cloudflare-release` and the exact currently working production image are
  the starting point. Check HEAD and recent Actions before a release.
- SQLite runs on local container storage. R2 `DATA/genesis.db` is the authoritative
  question snapshot; runtime/session/coaching snapshots use a separate key.
- Never operate SQLite over R2/FUSE. Never restore an old Drive pool, seed a pool,
  clean R2 prefixes, or replace production data with a development database.
- Preserve every existing protected row and R2 asset. A new schema may add fields
  or tables, but may not rewrite existing protected row values.
- Background/startup/session/coaching tasks cannot write the question snapshot.
- Explicit question additions must become durable before a successful save response.
- All devices/sessions read the same server pool. Do not cache pool data in
  localStorage, IndexedDB, service workers, or an HTTP cache.
- Read-only before/after protected SQLite fingerprints and R2 asset fingerprints
  are mandatory. A mismatch or production smoke failure triggers automatic image
  and Worker rollback, never a database rollback.
- Never remove the pool guard or its storage checks to make a build pass.
- Retain the previous working image and exact Worker source. Keep rollback verified.

Use `.github/workflows/cloudflare-runtime-recovery.yml` for protected releases.
Legacy release scripts must preserve this policy and pass the same integrity gate.
