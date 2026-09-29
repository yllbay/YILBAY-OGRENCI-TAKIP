from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_CONTAINER_ROOT","/app"))
p=root/"start-container.sh"
if not p.exists():
    raise SystemExit("start-container.sh missing")
new='''#!/bin/sh
set -eu
# GENESIS_LOCAL_SQLITE_RUNTIME_V1
# Question Studio SQLite must never run on an R2/FUSE mount.
mkdir -p /app/DATA
cd /app/APP/backend
exec python -m uvicorn app:app --host 0.0.0.0 --port 8000
'''
p.write_text(new,encoding="utf-8")
p.chmod(0o755)
print("GENESIS local SQLite runtime start script installed")
