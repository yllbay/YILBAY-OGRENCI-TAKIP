# ANA PRG E2E — candidate evidence

Automated disposable suite: 10 integration tests cover schema/cold restore,
transaction rollback, auth/CSRF/ownership/expiry, PIN lock, weekly generation/
sync/order/reset, upload/assignment/submission/key/grading/review, whole TYT/AYT
count/single-call/history, low-confidence/recovery, WhatsApp opt-in/deduplication,
batch/item-analysis/safe CSV, native routes/archive dependencies. Provider adapters
in this suite are mocks; this is not proof of actual provider delivery.

Manual real-browser preview: teacher login, class/student CRUD, course selection,
homework creation and all native navigation screens are being exercised.
Full-image Chromium suite additionally covers 1366x768, 1920x1080 and 390x844,
weekly generation, 120-question key entry, a separate student browser and teacher
endpoint rejection. Full-image CI results are pending.

Actual OpenAI Responses tests used synthetic complete TYT120, AYT80 scientific
and AYT80 verbal optical images with independently known answers. Each image was
read in exactly one Luna call. Scientific matched all answers. TYT/verbal showed
confident blank-row errors in repeated fixtures; a stronger prompt did not reliably
eliminate them. All optical reports now require teacher review, followed by
deterministic recalculation; original raw/normalized output is retained.
Do not describe raw OCR ground-truth accuracy as PASS for the failing fixtures.

Pending: actual homework key/evaluation provider flow, reviewed optical history
and browser upload proof, actual Meta controlled delivery, actual R2/cold restart,
authenticated production smoke and final Question Studio regression gate.
