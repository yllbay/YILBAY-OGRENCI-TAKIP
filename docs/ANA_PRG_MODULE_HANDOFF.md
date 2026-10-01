# ANA PRG native module handoff

Status: candidate implementation; production activation and acceptance pending.

Functional baseline: ANA PRG @38, v5.1.3.4. The human user's revised scope
requires all features independent of Google, with no legacy student/PDF/history
import. Existing Apps Script, Sheets and Drive remain unchanged.

Routes: `/ana-prg`, `/program`, `/classes`, `/homework`, `/assignments`,
`/submissions`, `/ai`, `/whatsapp`, `/mock-exams`, `/reports`, `/settings`,
`/system`, `/student`, all under `/ana-prg`. APIs are under `/api/ana-prg`.
The module uses the existing GENESIS layout/navigation and retires coaching routes.

The backend package is `cloudflare/ana_prg/`; installers copy it into the current
production image without reading/writing GENESIS data. Its local SQLite path is
`/app/ANA_RUNTIME/ana.db`; R2 snapshot `ANA_PRG/runtime/ana.db`; uploads are
immutable `ANA_PRG/files/<category>/<sha256>.<extension>` objects. Successful
mutations require a conditional R2 snapshot before the SQLite commit/HTTP response.
No source API or Google authorization is required to operate the new module.

Teacher login verifies the existing GENESIS administrator password; automatic
legacy ADMIN cookies are insufficient. Students use their ANA code and PIN with
an independent, scoped, expiring session. Create classes/students, upload new
homework PDFs, set course rules, then generate/sync a week. Empty data is intentional.

AI uses `OPENAI_API_KEY`; the default Luna model is `gpt-5.6-luna`. Keys are
teacher-reviewed. A whole optical PNG/JPEG is submitted once, all sections are
read in one call, counts are validated, and deterministic grading creates one
review report. **Every AI optical report requires explicit teacher approval**:
actual provider fixtures showed confident blank-row misreads. Approval exposes
the corrected report in student history. The original provider output remains
auditable. Interrupted calls become UNCERTAIN and are never silently replayed.

WhatsApp requires `ANA_WHATSAPP_ACCESS_TOKEN`, `ANA_WHATSAPP_PHONE_NUMBER_ID`,
an approved provider template and a dated recipient opt-in. Sending is explicit,
deduplicated and budget-limited. Default shadow mode blocks external calls and
WhatsApp is disabled. Secrets are environment/Worker secrets, never form settings.
The user subsequently deferred WhatsApp connection; real Meta activation/delivery
is intentionally excluded from the current acceptance, with the native workflow retained.

Use the protected recovery workflow with `[ana-prg] [pool-candidate]` for a
candidate only. It extracts the exact live image, installs code and runs disposable
unit, integration, browser and restart checks. Only a verified image may be
activated with `[ana-prg] [pool-release]`. Refresh current Question Studio baselines.
Any failed critical production gate must restore the captured exact Worker and
image; do not restore a DB or delete ANA/source data. The permanent encrypted
GENESIS 2026-10-01 checkpoint and its key must remain intact.

Pending release gates: full-image CI, actual R2 cold restore/file verification,
authenticated production teacher/student browser smoke, Meta safe delivery test,
production integrity comparison and final evidence documents. Source shutdown
has not been requested and is outside this deployment.
