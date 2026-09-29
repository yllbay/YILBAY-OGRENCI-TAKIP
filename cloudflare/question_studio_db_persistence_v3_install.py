from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"db.py"
src=path.read_text(encoding="utf-8")
mark="GENESIS_QUESTION_STUDIO_DB_PERSIST_V3_BOOTSTRAP"
if mark in src:
    raise SystemExit(0)
if "GENESIS_QUESTION_STUDIO_DB_PERSIST_V2" not in src:
    raise SystemExit("V2 persistence marker missing")

src=src.replace(
    "from r2_object_store import persist_primary_db, restore_primary_db",
    "from r2_object_store import persist_primary_db, restore_primary_db, head as r2_head",
    1,
)

src=src.replace(
    'if os.environ.get("R2_ACCOUNT_ID") and not DB.exists():\n    restore_primary_db(DB)',
    'if os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")!="1" and not DB.exists():\n    restore_primary_db(DB)',
    1,
)

src=src.replace(
    '''def _persist_primary_snapshot(target:Path):
    if not os.environ.get("R2_ACCOUNT_ID"):
        return False
    if target.resolve()!=DB.resolve() or not target.exists():
''',
    '''def _persist_primary_snapshot(target:Path):
    if os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")=="1":
        return False
    if target.resolve()!=DB.resolve() or not target.exists():
''',
    1,
)

anchor='''

def _cols(con,table):
'''
bootstrap='''

# GENESIS_QUESTION_STUDIO_DB_PERSIST_V3_BOOTSTRAP
def _bootstrap_primary_snapshot():
    if os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")=="1":
        return False
    if not DB.exists():
        return False
    meta=r2_head("DATA/genesis.db")
    if meta and int(meta.get("size") or 0)>0:
        return True
    return _persist_primary_snapshot(DB)

_bootstrap_primary_snapshot()

def _cols(con,table):
'''
if anchor not in src:
    raise SystemExit("db helper anchor changed")
src=src.replace(anchor,bootstrap,1)

old_tail='''    if changed:
        _persist_primary_snapshot(target)
'''
new_tail='''    if changed:
        _persist_primary_snapshot(target)
    elif os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")!="1" and target.resolve()==DB.resolve() and not r2_head("DATA/genesis.db"):
        _persist_primary_snapshot(target)
'''
if old_tail not in src:
    raise SystemExit("db persist tail anchor changed")
src=src.replace(old_tail,new_tail,1)

path.write_text(src,encoding="utf-8")
