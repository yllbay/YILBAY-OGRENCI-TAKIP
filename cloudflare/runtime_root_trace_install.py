from pathlib import Path
import os

root=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
p=root/"backend"/"app.py"
src=p.read_text(encoding="utf-8")
MARK="GENESIS_RUNTIME_ROOT_TRACE_V1"
if MARK in src:
    raise SystemExit(0)

lines=src.splitlines()
start=end=None
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
    raise SystemExit("FastAPI app construction anchor changed")

block=r'''
# GENESIS_RUNTIME_ROOT_TRACE_V1
@app.middleware("http")
async def genesis_runtime_root_trace(request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        if request.headers.get("x-genesis-runtime-diagnostic")=="root-v1":
            import traceback
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=590,
                content={
                    "marker":"GENESIS_RUNTIME_ROOT_TRACE_V1",
                    "exception_type":type(exc).__name__,
                    "detail":str(exc)[:1200],
                    "traceback":traceback.format_exc().splitlines()[-60:],
                },
            )
        raise
'''
lines.insert(end+1,block)
p.write_text("\n".join(lines)+"\n",encoding="utf-8")
assert MARK in p.read_text(encoding="utf-8")
print("GENESIS runtime root trace diagnostic installed")
