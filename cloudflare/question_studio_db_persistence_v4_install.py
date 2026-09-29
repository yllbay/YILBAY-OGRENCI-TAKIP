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

# Normalize legacy V3 variants: isolated/test mode must bypass every R2 write.
persist_def='def _persist_primary_snapshot(target:Path):'
skip_line='    if os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")=="1":\n        return False\n'
pos=src.find(persist_def)
if pos<0:
    raise SystemExit("primary snapshot helper missing")
body_start=pos+len(persist_def)
body_preview=src[body_start:body_start+220]
if 'GENESIS_SKIP_R2_SNAPSHOT' not in body_preview:
    src=src[:body_start]+"\n"+skip_line+src[body_start:].lstrip("\n")

# Startup/restart/deploy may restore the authoritative R2 DB, but must never
# create or rewrite the primary snapshot merely because the container started.
# Disposable tests explicitly opt out of all R2 access.
src=src.replace(
    'if not DB.exists():\n    restore_primary_db(DB)',
    'if os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")!="1" and not DB.exists():\n    restore_primary_db(DB)',
    1,
)
src=src.replace("\n_bootstrap_primary_snapshot()\n","\n# V4: startup snapshot creation disabled; restore remains read-only.\n",1)

old='''    elif os.environ.get("GENESIS_SKIP_R2_SNAPSHOT")!="1" and target.resolve()==DB.resolve() and not r2_head("DATA/genesis.db"):
        _persist_primary_snapshot(target)
'''
if old in src:
    src=src.replace(old,"",1)

src += "\n# "+MARK+"\n"
path.write_text(src,encoding="utf-8")
print("GENESIS DB persistence V4 no-startup-write installed")
