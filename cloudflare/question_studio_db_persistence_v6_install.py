from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"db.py"
src=path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_DB_PERSIST_V6_CENTRAL_BOOTSTRAP"
if MARK in src:
    raise SystemExit(0)
if "GENESIS_QUESTION_STUDIO_DB_PERSIST_V5_USER_SCOPED" not in src:
    raise SystemExit("V5 persistence marker missing")

anchor="# GENESIS_QUESTION_STUDIO_DB_PERSIST_V4_NO_STARTUP_WRITE"
if anchor not in src:
    raise SystemExit("V4 marker missing")

bootstrap=r'''
# GENESIS_QUESTION_STUDIO_DB_PERSIST_V6_CENTRAL_BOOTSTRAP
# Read-through centralization: never change logical Question Studio content.
# If a central snapshot exists, it wins. If it does not, copy the current DB
# byte-for-byte once so every future container/device starts from one source.
def _genesis_centralize_primary_db():
    if os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")=="1":
        return
    if not DB.exists():
        restore_primary_db(DB)
        return
    meta=r2_head("DATA/genesis.db")
    if meta and int(meta.get("size") or 0)>0:
        tmp=DB.with_suffix(".central.restore")
        if restore_primary_db(tmp):
            os.replace(tmp,DB)
        return
    persist_primary_db(DB)

_genesis_centralize_primary_db()
'''
src=src.replace("\n# "+anchor+"\n","\n"+bootstrap+"\n# "+anchor+"\n",1)
path.write_text(src,encoding="utf-8")
print("GENESIS central R2 DB bootstrap installed")
