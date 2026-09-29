from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
db_path=root/"backend"/"db.py"
app_path=root/"backend"/"app.py"
db=db_path.read_text(encoding="utf-8")
app=app_path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_HARD_LOCK_V1"

if MARK in db and MARK in app:
    print("question studio hard lock already installed")
    raise SystemExit(0)

# ---- DB layer: deny background/startup/deploy writes to existing Question Studio tables.
if MARK not in db:
    ctx_anchor='CURRENT_INSTITUTION_ID=contextvars.ContextVar("genesis_current_institution_id",default=None)'
    if ctx_anchor not in db:
        raise SystemExit("db context anchor changed; refusing unsafe hard-lock patch")
    ctx_insert=ctx_anchor+'''

# GENESIS_QUESTION_STUDIO_HARD_LOCK_V1
# Existing Question Studio data is immutable for startup/deploy/background code.
# Mutations are allowed only while handling an explicit non-read-only HTTP request.
QUESTION_STUDIO_USER_WRITE=contextvars.ContextVar("genesis_question_studio_user_write",default=False)

def _question_studio_protected_table(name):
    n=str(name or "").lower()
    return (
        "question" in n
        or "topic" in n
        or n=="exams"
        or n.startswith("exam_")
        or n=="tests"
        or n.startswith("test_")
    )

_QS_DENY_ACTIONS={
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_DROP_TABLE,
}
'''
    db=db.replace(ctx_anchor,ctx_insert,1)

    row_anchor='con.row_factory=sqlite3.Row'
    db_lines=db.splitlines()
    row_idx=None
    for i,line in enumerate(db_lines):
        if row_anchor in line:
            row_idx=i
            break
    if row_idx is None:
        raise SystemExit("db connection anchor changed; refusing unsafe hard-lock patch")
    indent=db_lines[row_idx][:len(db_lines[row_idx])-len(db_lines[row_idx].lstrip())]
    block=[
        "# Protect only tables that already exist. This permits first-time schema creation",
        "# while making existing Question Studio content immutable outside user requests.",
        "_qs_existing={",
        "    str(r[0]).lower()",
        "    for r in con.execute(\"select name from sqlite_master where type='table'\").fetchall()",
        "}",
        "_qs_protected={n for n in _qs_existing if _question_studio_protected_table(n)}",
        "def _qs_authorizer(action,arg1,arg2,db_name,trigger_name):",
        "    if QUESTION_STUDIO_USER_WRITE.get():",
        "        return sqlite3.SQLITE_OK",
        "    table=str(arg1 or \"\").lower()",
        "    if action in _QS_DENY_ACTIONS and table in _qs_protected:",
        "        return sqlite3.SQLITE_DENY",
        "    return sqlite3.SQLITE_OK",
        "con.set_authorizer(_qs_authorizer)",
    ]
    db_lines[row_idx+1:row_idx+1]=[indent+x for x in block]
    db="\n".join(db_lines)+"\n"
    db_path.write_text(db,encoding="utf-8")

# ---- HTTP layer: explicit user mutations get a scoped write token.
if MARK not in app:
    # Add the context variable to the existing db import.
    import_anchor='from db import init_db, connect, log_event, audit, ROOT, DATA, DB, SCHEMA_VERSION, format_folder_name, CURRENT_DB, CURRENT_INSTITUTION_ID'
    if import_anchor not in app:
        raise SystemExit("db import anchor changed; refusing unsafe hard-lock patch")
    app=app.replace(import_anchor,import_anchor+', QUESTION_STUDIO_USER_WRITE',1)

    # Find the complete FastAPI construction expression. Never inject into the middle
    # of a multiline constructor: if structure is unexpected, fail the build.
    lines=app.splitlines()
    start=None
    end=None
    balance=0
    for i,line in enumerate(lines):
        if start is None and "FastAPI(" in line and "=" in line and not line.lstrip().startswith("#"):
            start=i
        if start is not None:
            balance += line.count("(")-line.count(")")
            if balance<=0:
                end=i
                break
    if start is None or end is None:
        raise SystemExit("FastAPI app construction anchor changed; refusing unsafe hard-lock patch")

    middleware=r'''
# GENESIS_QUESTION_STUDIO_HARD_LOCK_V1
@app.middleware("http")
async def genesis_question_studio_write_scope(request, call_next):
    mutating=request.method.upper() not in {"GET","HEAD","OPTIONS"}
    token=QUESTION_STUDIO_USER_WRITE.set(bool(mutating))
    try:
        return await call_next(request)
    finally:
        QUESTION_STUDIO_USER_WRITE.reset(token)

def _genesis_qs_fingerprint_payload():
    import hashlib, json
    with connect() as con:
        names=[
            str(r[0]) for r in con.execute(
                "select name from sqlite_master where type='table' order by name"
            ).fetchall()
        ]
        protected=[n for n in names if (
            "question" in n.lower()
            or "topic" in n.lower()
            or n.lower()=="exams"
            or n.lower().startswith("exam_")
            or n.lower()=="tests"
            or n.lower().startswith("test_")
        )]
        tables={}
        for name in protected:
            qname='"'+name.replace('"','""')+'"'
            cols=[str(r[1]) for r in con.execute(f"pragma table_info({qname})").fetchall()]
            rows=[list(r) for r in con.execute(f"select * from {qname} order by rowid").fetchall()]
            raw=json.dumps(
                {"columns":cols,"rows":rows},
                ensure_ascii=False,separators=(",",":"),default=str
            ).encode("utf-8")
            tables[name]={"count":len(rows),"sha256":hashlib.sha256(raw).hexdigest()}
        aggregate=json.dumps(tables,sort_keys=True,separators=(",",":")).encode("utf-8")
        return {
            "marker":"GENESIS_QUESTION_STUDIO_HARD_LOCK_V1",
            "protected_tables":tables,
            "sha256":hashlib.sha256(aggregate).hexdigest(),
        }

@app.get("/api/internal/question-studio-fingerprint")
def genesis_question_studio_fingerprint():
    # Read-only. Used by CI to prove deploy/restart did not alter folders/questions/exams.
    return _genesis_qs_fingerprint_payload()
'''
    lines.insert(end+1,middleware)
    app="\n".join(lines)+"\n"
    app_path.write_text(app,encoding="utf-8")

out_db=db_path.read_text(encoding="utf-8")
out_app=app_path.read_text(encoding="utf-8")
assert MARK in out_db
assert MARK in out_app
assert "QUESTION_STUDIO_USER_WRITE" in out_db
assert "/api/internal/question-studio-fingerprint" in out_app
print("GENESIS Question Studio hard lock installed")
