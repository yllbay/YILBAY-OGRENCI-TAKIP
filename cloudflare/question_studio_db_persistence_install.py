from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"db.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_DB_PERSIST_V1"
if mark in src:
    raise SystemExit(0)

src=src.replace(
    "import contextvars\nfrom pathlib import Path\nfrom contextlib import contextmanager\n",
    "import contextvars\nimport tempfile, os\nfrom pathlib import Path\nfrom contextlib import contextmanager\nfrom r2_object_store import persist_primary_db, restore_primary_db\n",
    1,
)
src=src.replace(
    'DATA=ROOT/"DATA"\\nDB=DATA/"genesis.db"\\n',
    '''# GENESIS_QUESTION_STUDIO_DB_PERSIST_V1
DATA=Path(os.environ.get("GENESIS_RUNTIME_DATA_DIR","/app/GENESIS_RUNTIME_DATA"))
DB=DATA/"genesis.db"
DATA.mkdir(parents=True,exist_ok=True)
if os.environ.get("R2_ACCOUNT_ID") and not DB.exists():
    restore_primary_db(DB)
''',
    1,
)
anchor='CURRENT_INSTITUTION_ID=contextvars.ContextVar("genesis_current_institution_id",default=None)\n'
helper=anchor+'''
# GENESIS_QUESTION_STUDIO_DB_PERSIST_V1
def _persist_primary_snapshot(target:Path):
    if target.resolve()!=DB.resolve() or not target.exists():
        return False
    fd,name=tempfile.mkstemp(prefix="genesis-snap-",suffix=".db")
    os.close(fd)
    tmp=Path(name)
    try:
        source=sqlite3.connect(target,timeout=20)
        snapshot=sqlite3.connect(tmp)
        try:
            source.backup(snapshot)
        finally:
            snapshot.close()
            source.close()
        persist_primary_db(tmp)
        return True
    finally:
        tmp.unlink(missing_ok=True)
'''
if anchor not in src:
    raise SystemExit("db context anchor changed")
src=src.replace(anchor,helper,1)

old='''    try:
        yield con
        con.commit()
    finally:
        con.close()
'''
new='''    changed=False
    try:
        yield con
        changed=con.total_changes>0
        con.commit()
    finally:
        con.close()
    if changed:
        _persist_primary_snapshot(target)
'''
if old not in src:
    raise SystemExit("db connect anchor changed")
path.write_text(src.replace(old,new,1),encoding="utf-8")
