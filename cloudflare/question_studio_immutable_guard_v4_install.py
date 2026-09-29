from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
db_path=root/"backend"/"db.py"
db=db_path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_IMMUTABLE_GUARD_V4_AUTHORIZE_ALL_CONNECTIONS"

if MARK in db:
    print("Question Studio immutable guard V4 already installed")
    raise SystemExit(0)
if "GENESIS_QUESTION_STUDIO_HARD_LOCK_V1" not in db:
    raise SystemExit("V1 hard lock missing; refusing unsafe V4 patch")

helper_anchor='''_QS_DENY_ACTIONS={
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_DROP_TABLE,
}
'''
helper=helper_anchor+'''

def _qs_install_authorizer(con):
    """Attach immutable Question Studio policy to every SQLite connection."""
    existing={
        str(r[0]).lower()
        for r in con.execute("select name from sqlite_master where type='table'").fetchall()
    }
    protected={n for n in existing if _question_studio_protected_table(n)}
    def _authorizer(action,arg1,arg2,db_name,trigger_name):
        if QUESTION_STUDIO_USER_WRITE.get():
            return sqlite3.SQLITE_OK
        table=str(arg1 or "").lower()
        if action in _QS_DENY_ACTIONS and table in protected:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    con.set_authorizer(_authorizer)
    return con
'''
if helper_anchor not in db:
    raise SystemExit("hard-lock deny set anchor changed")
db=db.replace(helper_anchor,helper,1)

lines=db.splitlines()
out=[]
installed=0
for i,line in enumerate(lines):
    out.append(line)
    if "con.row_factory=sqlite3.Row" not in line:
        continue
    indent=line[:len(line)-len(line.lstrip())]
    # Do not duplicate an immediately existing V4 call.
    nxt=lines[i+1] if i+1<len(lines) else ""
    if "_qs_install_authorizer(con)" in nxt:
        continue
    out.append(indent+"_qs_install_authorizer(con)")
    installed+=1

if installed<1:
    raise SystemExit("no SQLite row_factory connection anchors found")
db="\n".join(out)+"\n# "+MARK+"\n"
db_path.write_text(db,encoding="utf-8")

check=db_path.read_text(encoding="utf-8")
assert MARK in check
assert "def _qs_install_authorizer(con):" in check
assert check.count("_qs_install_authorizer(con)")>=2  # definition + at least one call
print(f"GENESIS Question Studio immutable guard V4 installed on {installed} connection path(s)")
