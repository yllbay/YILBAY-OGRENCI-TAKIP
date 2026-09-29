from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
app_path=root/"backend"/"app.py"
app=app_path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V3"

if MARK in app:
    print("Question Studio immutable guard V3 already installed")
    raise SystemExit(0)
if "GENESIS_QUESTION_STUDIO_HARD_LOCK_V1" not in app:
    raise SystemExit("V1 hard lock missing; refusing unsafe V3 patch")

old='''    mutating=request.method.upper() not in {"GET","HEAD","OPTIONS"}
    token=QUESTION_STUDIO_USER_WRITE.set(bool(mutating))
'''
new='''    method=request.method.upper()
    path=request.url.path
    mutating=method not in {"GET","HEAD","OPTIONS"}
    # GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V3
    # Only explicit Question Studio user endpoints may open the DB write scope.
    # All deploy/startup/background/coaching/admin traffic remains read-only
    # with respect to protected Question Studio tables.
    qs_prefixes=(
        "/api/questions", "/api/question",
        "/api/topics", "/api/topic",
        "/api/tests", "/api/test-", "/api/test/",
        "/api/exams", "/api/exam",
        "/api/crops", "/api/crop",
        "/api/sources", "/api/source",
        "/api/prepared", "/api/finalize",
    )
    user_qs_write=bool(mutating and path.startswith(qs_prefixes))
    token=QUESTION_STUDIO_USER_WRITE.set(user_qs_write)
'''
if old not in app:
    raise SystemExit("hard-lock middleware shape changed; refusing unsafe V3 patch")
app=app.replace(old,new,1)
app += "\n# "+MARK+"\n"
app_path.write_text(app,encoding="utf-8")
print("GENESIS Question Studio immutable guard V3 installed")
