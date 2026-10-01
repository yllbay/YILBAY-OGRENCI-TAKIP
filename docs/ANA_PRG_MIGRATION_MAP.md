# ANA PRG native web contract

## Authorized scope (2026-10-01)

The user's subsequent instruction supersedes historical data/file migration:
implement every program feature on the web, independent of Drive. Do not import
existing students, homework PDFs, assignments or historical records. Source
deployment @38 / v5.1.3.4 is the functional baseline. Source systems remain intact.
The latest ZIP is not a data migration dependency in this revised scope; the
@38 source and local QA/deployment handoff have been inspected.

## Storage ownership

Local SQLite `/app/ANA_RUNTIME/ana.db` contains only `ana_*` tables. R2 snapshot
`ANA_PRG/runtime/ana.db` is independent of GENESIS `DATA/genesis.db` and
`_runtime/operations.db`. ANA code cannot open, restore or write the question DB.
Uploads use immutable SHA-256 object keys under `ANA_PRG/files/`. Each file has
size, MIME, checksum and server-authorized ownership. No Google APIs are needed
at runtime. Source/target data and file import counts are intentionally zero.

## Feature mapping

| Source | Native contract |
|---|---|
| Dashboard/RPC | `/api/ana-prg/dashboard`, aggregate SQL and recent activity |
| SINIF_DB / ÖĞRENCİ_DB | `ana_classes`, `ana_students`, archive, course selection, guardian opt-in, code + PIN |
| Weekly sheet/rules | `ana_programs`, `ana_program_slots`, `ana_course_rules`; explicit dates, selected courses, previous actual program slots determine used PDFs, deterministic assignment IDs |
| ÖDEV_DB | `ana_homework_pool`, authorized R2 PDF upload/index and topic/test order |
| ATAMA_DB / TESLİM_DB | `ana_assignments`, `ana_submissions`, status, deadlines, authorized upload |
| CEVAP_ANAHTARI / AI_DEĞERLENDİRME / AI_KUYRUK | `ana_answer_keys`, `ana_ai_evaluations`, `ana_ai_queue`, durable jobs, reference assets, deterministic marking, review, cost telemetry |
| VIDEO / KONU_SIRA / İLERLEME | `ana_videos`, `ana_topic_order`, derived progress API |
| VELİ / WhatsApp / templates | `ana_guardians`, `ana_whatsapp_queue`, `ana_whatsapp_templates`, opt-in validation, explicit send, ambiguous delivery is not automatically retried |
| Deneme exams / optics / results | `ana_mock_exams`, `ana_mock_optics`, `ana_mock_results`; exactly one Responses call for a complete optical image, strict section counts, D−Y/4, manual review/recalculation, history/trend/item analysis, batch jobs |
| Reports/cost/log/settings | `ana_weekly_reports`, `ana_costs`, `ana_audit_log`, `ana_settings`, UTF-8 safe CSV |
| Student portal | module-scoped HttpOnly session; ownership enforced for programs/submissions/AI/results/files |

All 12 areas have native `/ana-prg/*` pages. Coaching routes and navigation are
retired without deleting old records. Question Studio and other modules retain
their routes. Existing automatic GENESIS ADMIN sessions cannot grant ANA access:
teacher access additionally requires proof of a real GENESIS administrator login.
Students have separate sessions, 5-attempt / 15-minute lockout, 60-minute expiry.

## Release acceptance

Run schema/domain/API/browser/security/persistence tests on disposable data.
Provider-mocked tests are labelled as such; actual OpenAI/Meta checks are separate
and cannot be reported PASS unless executed. The existing protected workflow
must capture current protected SQLite/R2 fingerprints and compare after rollout.
Any critical release failure rolls back the exact previous image and Worker,
never a database snapshot. No test questions or source records are mutated.
