from pathlib import Path
import os

root = Path(os.environ.get('GENESIS_APP_ROOT', '/app/APP'))
app = root / 'backend' / 'app.py'
if not app.is_file():
    raise SystemExit(f'app.py missing: {app}')

mark = 'GENESIS_COACHING_DATA_MODEL_V1_START'
s = app.read_text(encoding='utf-8')
if mark not in s:
    anchor = '# GENESIS_COACHING_CURRICULUM_STEP1_END\n'
    block = '''# GENESIS_COACHING_CURRICULUM_STEP1_END

# GENESIS_COACHING_DATA_MODEL_V1_START
from coaching_data_model_v1 import install_coaching_data_model_v1
install_coaching_data_model_v1(app=app)
# GENESIS_COACHING_DATA_MODEL_V1_END
'''
    if anchor not in s:
        raise SystemExit('curriculum install anchor missing')
    s = s.replace(anchor, block, 1)
    app.write_text(s, encoding='utf-8')

out = app.read_text(encoding='utf-8')
assert mark in out
assert 'install_coaching_data_model_v1(app=app)' in out
print('GENESIS coaching data model install patch: OK')
