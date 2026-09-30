from pathlib import Path
import os
import re
import sys

root = Path(os.getenv('GENESIS_CONTAINER_ROOT', '/app'))
backend = root / 'APP/backend'
app_path = backend / 'app.py'
src = app_path.read_text(encoding='utf-8')
if 'GENESIS_LOCAL_SQLITE_R2_V1' in src:
    print('Local SQLite runtime hooks already installed')
    sys.exit(0)
src = src.replace('import fitz', 'from starlette.concurrency import run_in_threadpool\nimport runtime_storage\nimport fitz', 1)
src = src.replace('    path=request.url.path\n', '''    path=request.url.path
    # Health probes must never acquire SQLite locks or create sessions.
    if path=="/_health":
        return JSONResponse({"ok":True,"runtime":"GENESIS_LOCAL_SQLITE_R2_V1",**runtime_storage.status()})
''', 1)
src = src.replace('    session=session_from_token(token)', '    session=await run_in_threadpool(session_from_token,token)', 1)
src = src.replace('        auto_admin_token=create_session("ADMIN")\n        session=session_from_token(auto_admin_token)',
    '        auto_admin_token=await run_in_threadpool(create_session,"ADMIN")\n        session=await run_in_threadpool(session_from_token,auto_admin_token)', 1)
# Run external cleanup after readiness, without blocking the ASGI event loop.
names = ['purge_pending_deletions_on_startup', 'purge_stale_prepared_on_startup',
         'purge_finalized_working_files_on_startup', 'purge_transient_source_files_on_startup']
for name in names:
    anchor = '@app.on_event("startup")\ndef ' + name + '():'
    assert anchor in src, name
    src = src.replace(anchor, 'def ' + name + '():', 1)
src += '''

# GENESIS_LOCAL_SQLITE_R2_V1
@app.on_event("startup")
def genesis_runtime_storage_start():
    runtime_storage.start()
    def maintenance():
        for operation in (purge_pending_deletions_on_startup,purge_stale_prepared_on_startup,
                          purge_finalized_working_files_on_startup,purge_transient_source_files_on_startup):
            try:
                operation()
            except Exception as error:
                print("GENESIS maintenance error",type(error).__name__,flush=True)
    threading.Thread(target=maintenance,name="genesis-maintenance",daemon=True).start()

@app.on_event("shutdown")
def genesis_runtime_storage_stop():
    runtime_storage.stop()

@app.middleware("http")
async def genesis_runtime_persist(request,call_next):
    response=await call_next(request)
    if request.method in {"POST","PUT","PATCH","DELETE"} and response.status_code<400:
        await run_in_threadpool(runtime_storage.sync_once)
    return response
'''
app_path.write_text(src, encoding='utf-8')
start = root / 'start-container.sh'
start.write_text('''#!/bin/sh
set -eu
if [ -L /app/DATA ]; then unlink /app/DATA; fi
mkdir -p /app/DATA
export GENESIS_PUBLIC_GATEWAY=0
cd /app/APP/backend
exec python runtime_storage.py
''', encoding='utf-8')
start.chmod(0o755)
print('GENESIS local SQLite, isolated health, and R2 persistence installed')
