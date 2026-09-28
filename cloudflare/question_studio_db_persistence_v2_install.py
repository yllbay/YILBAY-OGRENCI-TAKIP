from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"db.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_DB_PERSIST_V2"
if mark in src:
    raise SystemExit(0)

src=src.replace(
    "import contextvars",
    "import contextvars\nimport tempfile, os\nfrom r2_object_store import persist_primary_db, restore_primary_db",
    1,
)
src=src.replace(
    'DATA=ROOT/"DATA"',
    '# GENESIS_QUESTION_STUDIO_DB_PERSIST_V2\nDATA=Path(os.environ.get("GENESIS_RUNTIME_DATA_DIR","/app/GENESIS_RUNTIME_DATA"))',
    1,
)
src=src.replace(
    'DB=DATA/"genesis.db"',
    'DB=DATA/"genesis.db"\nDATA.mkdir(parents=True,exist_ok=True)\nif os.environ.get("R2_ACCOUNT_ID") and not DB.exists():\n    restore_primary_db(DB)',
    1,
)

anchor='CURRENT_INSTITUTION_ID=contextvars.ContextVar("genesis_current_institution_id",default=None)'
helper=anchor+'''

def _persist_primary_snapshot(target:Path):
    if not os.environ.get("R2_ACCOUNT_ID"):
        return False
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
src=src.replace(old,new,1)
path.write_text(src,encoding="utf-8")
