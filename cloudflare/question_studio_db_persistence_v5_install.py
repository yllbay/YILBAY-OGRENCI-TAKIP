from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"db.py"
src=path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_DB_PERSIST_V5_USER_SCOPED"

if MARK in src:
    print("DB persistence V5 already installed")
    raise SystemExit(0)
if "GENESIS_QUESTION_STUDIO_DB_PERSIST_V4_NO_STARTUP_WRITE" not in src:
    raise SystemExit("V4 persistence marker missing")
if "GENESIS_QUESTION_STUDIO_HARD_LOCK_V1" not in src:
    raise SystemExit("Question Studio hard-lock marker missing")

old='''    if changed:
        _persist_primary_snapshot(target)
'''
new='''    # GENESIS_QUESTION_STUDIO_DB_PERSIST_V5_USER_SCOPED
    # Never let auth/session/coaching/startup/background writes touch the
    # authoritative Question Studio snapshot. Persist it only after an explicit
    # user mutation routed through Question Studio write scope.
    if changed and target.resolve()==DB.resolve() and QUESTION_STUDIO_USER_WRITE.get():
        _persist_primary_snapshot(target)
'''
if old not in src:
    raise SystemExit("connect persistence tail changed; refusing unsafe V5 patch")
src=src.replace(old,new,1)
path.write_text(src,encoding="utf-8")
print("GENESIS DB persistence V5 user-scoped snapshot installed")
