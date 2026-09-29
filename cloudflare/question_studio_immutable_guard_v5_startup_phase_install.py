from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
db_path=root/"backend"/"db.py"
app_path=root/"backend"/"app.py"
db=db_path.read_text(encoding="utf-8")
app=app_path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V5_STARTUP_PHASE"

if MARK in db and MARK in app:
    print("Question Studio immutable guard V5 startup phase already installed")
    raise SystemExit(0)

required=(
    "GENESIS_QUESTION_STUDIO_HARD_LOCK_V1",
    "GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V4_AUTHORIZE_ALL_CONNECTIONS",
)
for marker in required:
    if marker not in db:
        raise SystemExit(f"required DB marker missing: {marker}")

ctx='QUESTION_STUDIO_USER_WRITE=contextvars.ContextVar("genesis_question_studio_user_write",default=False)'
if "QUESTION_STUDIO_GUARD_ACTIVE=contextvars.ContextVar" not in db:
    if ctx not in db:
        raise SystemExit("Question Studio write context anchor changed")
    db=db.replace(
        ctx,
        ctx+'\nQUESTION_STUDIO_GUARD_ACTIVE=contextvars.ContextVar("genesis_question_studio_guard_active",default=True)',
        1,
    )

old='''    def _authorizer(action,arg1,arg2,db_name,trigger_name):
        if QUESTION_STUDIO_USER_WRITE.get():
            return sqlite3.SQLITE_OK
'''
new='''    def _authorizer(action,arg1,arg2,db_name,trigger_name):
        if (not QUESTION_STUDIO_GUARD_ACTIVE.get()) or QUESTION_STUDIO_USER_WRITE.get():
            return sqlite3.SQLITE_OK
'''
if old in db:
    db=db.replace(old,new,1)
elif new not in db:
    raise SystemExit("Question Studio authorizer shape changed")

# init_db may run idempotent schema/startup maintenance against the local runtime
# copy. It must never be blocked by the immutable authorizer, but it also must
# never acquire QUESTION_STUDIO_USER_WRITE, so V5 snapshot persistence stays off.
startup_block='''# GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V5_STARTUP_PHASE
import db as _genesis_qs_guard_db
_genesis_qs_guard_token=_genesis_qs_guard_db.QUESTION_STUDIO_GUARD_ACTIVE.set(False)
try:
    init_db()
finally:
    _genesis_qs_guard_db.QUESTION_STUDIO_GUARD_ACTIVE.reset(_genesis_qs_guard_token)
'''
if MARK not in app:
    lines=app.splitlines()
    idx=None
    for i,line in enumerate(lines):
        if line.strip()=="init_db()":
            idx=i
            break
    if idx is None:
        raise SystemExit("standalone init_db() anchor missing")
    indent=lines[idx][:len(lines[idx])-len(lines[idx].lstrip())]
    if indent:
        raise SystemExit("init_db() is unexpectedly nested; refusing unsafe patch")
    lines[idx:idx+1]=startup_block.rstrip("\n").splitlines()
    app="\n".join(lines)+"\n"

if MARK not in db:
    db += "\n# "+MARK+"\n"

db_path.write_text(db,encoding="utf-8")
app_path.write_text(app,encoding="utf-8")
out_db=db_path.read_text(encoding="utf-8")
out_app=app_path.read_text(encoding="utf-8")
assert MARK in out_db and MARK in out_app
assert "QUESTION_STUDIO_GUARD_ACTIVE" in out_db
assert "_genesis_qs_guard_db.QUESTION_STUDIO_GUARD_ACTIVE.set(False)" in out_app
assert "QUESTION_STUDIO_USER_WRITE.set(True)" not in startup_block
print("GENESIS Question Studio immutable guard V5 startup phase installed")
