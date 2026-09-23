from pathlib import Path

APP=Path('/app/APP/backend/app.py')
src=APP.read_text(encoding='utf-8')
MARK='GENESIS_COACHING_MODEL_V1_START'
if MARK in src:
    print('coaching model install already present')
    raise SystemExit(0)

needle='''# GENESIS_COACHING_03_START
from coaching_v2 import install_coaching_v2
install_coaching_v2(app=app, dist=DIST, log_fn=log_event)
# GENESIS_COACHING_03_END
'''

replacement=needle+'''
# GENESIS_COACHING_MODEL_V1_START
from coaching_model_v1 import install_coaching_model_v1
install_coaching_model_v1(app=app)
# GENESIS_COACHING_MODEL_V1_END
'''

if needle not in src:
    raise SystemExit('coaching_v2 install anchor missing')
APP.write_text(src.replace(needle,replacement,1),encoding='utf-8')
out=APP.read_text(encoding='utf-8')
assert MARK in out
assert 'install_coaching_model_v1(app=app)' in out
print('GENESIS coaching model app install patch: OK')
