from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
path=root/"backend"/"db.py"
src=path.read_text(encoding="utf-8")
MARK="GENESIS_QUESTION_STUDIO_DB_PERSIST_V4_NO_STARTUP_WRITE"

if MARK in src:
    print("DB persistence V4 already installed")
    raise SystemExit(0)
if "GENESIS_QUESTION_STUDIO_DB_PERSIST_V3_BOOTSTRAP" not in src:
    raise SystemExit("V3 persistence marker missing")

# Startup/restart/deploy may restore the authoritative R2 DB, but must never
# create or rewrite the primary snapshot merely because the container started.
src=src.replace("\n_bootstrap_primary_snapshot()\n","\n# V4: startup snapshot creation disabled; restore remains read-only.\n",1)

old='''    elif os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")!="1" and target.resolve()==DB.resolve() and not r2_head("DATA/genesis.db"):
        _persist_primary_snapshot(target)
'''
if old in src:
    src=src.replace(old,"",1)

src += "\n# "+MARK+"\n"
path.write_text(src,encoding="utf-8")
print("GENESIS DB persistence V4 no-startup-write installed")
