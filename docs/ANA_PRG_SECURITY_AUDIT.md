# ANA PRG security audit — candidate

Tested on disposable fixtures; production credential-backed checks pending.

* Every teacher mutation/read checks both a verified ANA administrator session
  and a valid GENESIS ADMIN session. Existing automatic ADMIN access cannot grant
  ANA access. Login is server-verified against the existing administrator hash.
* Teacher password change requires current-password proof and CSRF, persists
  in the existing operations snapshot, revokes teacher sessions, and preserves
  student sessions. The legacy GENESIS password endpoint now also requires
  current-password proof; an automatic ADMIN cookie cannot change the password.
* Student code/PIN is module-scoped. PBKDF2 SHA-256 (260,000 rounds), random salt,
  server token hashes, HttpOnly/SameSite cookies, one-hour expiry, five bad PIN
  attempts followed by a 15-minute lock. PIN changes and archiving revoke sessions.
* Student endpoints and file download enforce ownership. Teacher CRUD is denied
  to students. Unapproved AI results are hidden. ID-swapping negative tests pass.
* Mutation CSRF token and Origin validation; credentials and PINs never appear
  in responses/audit logs. The frontend escapes user-controlled text.
* File byte limits and server MIME/magic/parser verification reject invalid or
  encrypted PDF/images. Immutable generated R2 keys prevent supplied key traversal.
  Maximum file size is 20 MB; oversized chunked uploads are bounded.
* CSV formula prefixes are escaped; provider model data is structurally validated.
  Duplicate/missing answer numbers, subjects and unexpected choices fail closed.
* All entity relationships point to ANA tables. Deletes are reversible audited
  archives; class dependencies are checked; student sessions are revoked.
* Only ANA paths reach ANA snapshots/files. No protected question database writes,
  startup seeds, old snapshot loads, source deletes or production test questions.
* AI/WhatsApp are serialized, durable and budget-limited. Ambiguous provider
  outcomes are not automatically retried. WhatsApp requires opt-in and explicit send.

Material constraint: legacy GENESIS public automatic ADMIN behavior predates this
module. ANA adds verified-login proof and protects the GENESIS password-change
endpoint. Other existing GENESIS auth behavior is preserved.
No automatic certification or claim of a comprehensive penetration test is made.
