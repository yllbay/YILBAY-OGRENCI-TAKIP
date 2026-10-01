# ANA PRG data integrity — candidate

Baseline repository HEAD: `fe312c60d6a34d3fd829749d01fbe5a914e287bd`.
Live v115 image digest: `520be26036aede569368ed985a114e4220b022baf7bf7a8679579e0fd4d822d6`.
Worker version: `c742c1dd-e3f4-4256-a2bd-331ff29a7126`.

Protected Question Studio SQLite fingerprint:
`aeb4762b8020517dab638f59e68ea6d83c88d256f6e77c0be4838394be5da11d`.
Protected 14 R2 asset fingerprint:
`6882b92182ac93435ab1b0146f9f62f5229c0a3ab6d4fc439b1f030c6a1cc66d`.
Deployment must re-capture the current baseline and compare after activation.

The user explicitly removed historical student/data/PDF import from scope.
Source @38 inventory is a functional reference; zero legacy rows/files are imported.
The new module starts with zero business records. Synthetic fixtures stay in
disposable stores and are never loaded into production.

ANA SQLite contains `ana_*` tables only. Initialization is idempotent. Foreign key
checks, local snapshot restore, conditional snapshot conflict and failed-persist
rollback were exercised. New uploads use SHA-256 read-back verification and a
manifest in `ana_files`. Source systems and Question Studio data are untouched.

Pending: actual R2 file/cold-start evidence, full-image restart, production before/
after fingerprints and final image/commit identifiers. No final integrity PASS
is asserted until those gates complete.
