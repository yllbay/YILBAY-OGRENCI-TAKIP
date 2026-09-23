from pathlib import Path
import os

ROOT=Path(os.environ.get("GENESIS_APP_ROOT","/app/APP"))
APP=ROOT/"backend"/"app.py"
MARK="GENESIS_COACHING_MODEL_V3_INSTALL"
src=APP.read_text(encoding="utf-8")
if MARK in src:
    print("coaching model v3 install already present")
    raise SystemExit(0)

needle='''from coaching_v2 import install_coaching_v2
install_coaching_v2(app=app, dist=DIST, log_fn=log_event)
'''
replacement=needle+'''# GENESIS_COACHING_MODEL_V3_INSTALL
from coaching_model_v3 import install_coaching_model_v3
install_coaching_model_v3(app)
'''
if needle not in src:
    raise SystemExit("coaching_v2 install anchor missing")
APP.write_text(src.replace(needle,replacement,1),encoding="utf-8")
out=APP.read_text(encoding="utf-8")
assert MARK in out
assert "install_coaching_model_v3(app)" in out
print("GENESIS coaching model v3 app install: OK")
