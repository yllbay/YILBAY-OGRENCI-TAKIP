# ANA PRG performance — candidate

Entity list endpoints paginate/filter in SQL (100 default, 500 maximum). Indexed
student/course/week/status/exam columns and unique student/result/slot keys avoid
unbounded UI list rendering. SQLite lives on local disk, never an R2 mount.

Reads do not trigger a snapshot. Serialized mutations create a consistent snapshot
and conditionally persist it before acknowledgement. Jobs run outside the initiating
HTTP request, one provider call at a time, with bounded job batches and monthly
budget checks. Partial batch failures retain per-file results and idempotent jobs.

Uploads are read in 1 MB chunks with a 20 MB limit; the bounded image/PDF is buffered
for validation and the AI request. This implementation does not provide arbitrary
large-file streaming. Downloads currently buffer up to that same file limit.
Snapshots serialize the entire ANA database on writes; large institutional loads
need measurement before scaling this strategy. No latency/SLA claim is made.

Pending: measured SQL/dashboard/snapshot latency, full-image browser rendering,
actual R2 latency and production smoke timing. These are release evidence items,
not inferred from syntax checks.
