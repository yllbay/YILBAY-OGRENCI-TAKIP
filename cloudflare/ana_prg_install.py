"""Install native ANA code in extracted current image; preserve protected data."""
import os,re,shutil
from pathlib import Path
root=Path(os.environ.get('GENESIS_CONTAINER_ROOT','/app')).resolve()
backend=root/'APP/backend';dist=root/'APP/frontend/dist'
assert backend.is_dir() and dist.is_dir()
destination=backend/'ana_prg';source=Path(__file__).parent/'ana_prg'
shutil.copytree(source,destination,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
app_path=backend/'app.py';src=app_path.read_text(encoding='utf-8')
if '# ANA_PRG_NATIVE_V1' not in src:
    # Do not initialize any retired coaching services/background jobs or schemas.
    for start,end in [('GENESIS_COACHING_01_START','GENESIS_COACHING_01_END'),
                      ('GENESIS_COACHING_CURRICULUM_STEP1_START','GENESIS_COACHING_CURRICULUM_STEP1_END'),
                      ('GENESIS_COACHING_03_START','GENESIS_COACHING_03_END')]:
        pattern=r'# '+start+r'.*?# '+end
        assert len(re.findall(pattern,src,re.S))==1,start
        src=re.sub(pattern,'# '+start+'\n# Replaced by ANA PRG; archived tables are retained.\n# '+end,src,flags=re.S)
    # ANA owns all auth decisions; do not auto-create GENESIS ADMIN for its URLs.
    anchor='    # GENESIS_PUBLIC_TOKEN_ROUTE_ALLOWLIST_END\n'
    assert src.count(anchor)==1
    src=src.replace(anchor,anchor+'    public=public or path.startswith("/ana-prg") or path.startswith("/api/ana-prg")\n',1)
    auto='    if not session and not path.startswith("/coaching/student/")'
    assert src.count(auto)==1
    src=src.replace(auto,'    if not session and not path.startswith("/ana-prg") and not path.startswith("/api/ana-prg") and not path.startswith("/coaching/student/")',1)
    # ANA has its own durable transaction/snapshot. No GENESIS snapshot writes.
    anchor='    method=request.method.upper();path=request.url.path\n'
    assert src.count(anchor)==1
    src=src.replace(anchor,anchor+'    if path.startswith("/api/ana-prg") or path.startswith("/ana-prg"):\n        return await call_next(request)\n',1)
    src+='''

# ANA_PRG_NATIVE_V1
from ana_prg.api import install as install_ana_prg
ana_prg_service=install_ana_prg(app,DIST)
_ana_stop=threading.Event()
@app.on_event("startup")
def ana_start_scheduler():
    def scheduled():
        while not _ana_stop.wait(60):
            try:ana_prg_service.tick()
            except Exception as error:print("ANA scheduler",type(error).__name__,flush=True)
    threading.Thread(target=scheduled,name="ana-prg-jobs",daemon=True).start()
@app.on_event("shutdown")
def ana_stop_scheduler():_ana_stop.set()
'''
    app_path.write_text(src,encoding='utf-8')
js=dist/'app-0.10.7.js';body=js.read_text(encoding='utf-8')
body=body.replace('Koçluk Stüdyosu','ANA PRG · Eğitim Yönetimi').replace('location.href="/coaching"','location.href="/ana-prg"')
js.write_text(body,encoding='utf-8')
print('ANA_PRG_NATIVE_INSTALL_OK: only application source modified; no DATA/DB/R2 access')
