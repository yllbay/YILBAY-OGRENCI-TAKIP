from pathlib import Path

APP = Path('/app/APP/backend/app.py')
HTML = Path('/app/APP/frontend/dist/coaching-v2.html')
MARK = 'GENESIS_COACHING_HOT_ASSET_CACHE_V1'
ASSET_VER = '0.15.2-coaching-2'

for p in (APP, HTML):
    if not p.is_file():
        raise SystemExit(f'Expected production file missing: {p}')

# 1) Give changed coaching assets a new browser URL immediately.
html = HTML.read_text(encoding='utf-8')
import re
html2 = re.sub(r'/static/coaching-v2\.css\?v=[^"\']+', f'/static/coaching-v2.css?v={ASSET_VER}', html, count=1)
html2 = re.sub(r'/static/coaching-v2\.js\?v=[^"\']+', f'/static/coaching-v2.js?v={ASSET_VER}', html2, count=1)
if html2 == html and ASSET_VER not in html:
    raise SystemExit('Coaching asset version patch point not found')
HTML.write_text(html2, encoding='utf-8')

# 2) During active coaching development, never mark these two mutable files immutable.
src = APP.read_text(encoding='utf-8')
if MARK not in src:
    needle = '''    elif request.url.path.startswith("/static/"):
        if request.query_params.get("v"):
            response.headers["Cache-Control"]="public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"]="no-cache, must-revalidate, max-age=0"
'''
    replacement = '''    elif request.url.path.startswith("/static/"):
        # GENESIS_COACHING_HOT_ASSET_CACHE_V1
        # coaching-v2 is actively developed; do not let a stale immutable browser
        # cache hide production UI releases even when a version query is present.
        if request.url.path in ("/static/coaching-v2.js","/static/coaching-v2.css"):
            response.headers["Cache-Control"]="no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"]="no-cache"
            response.headers["Expires"]="0"
        elif request.query_params.get("v"):
            response.headers["Cache-Control"]="public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"]="no-cache, must-revalidate, max-age=0"
'''
    if needle not in src:
        raise SystemExit('Static cache middleware patch point not found')
    src = src.replace(needle, replacement, 1)
    APP.write_text(src, encoding='utf-8')

# Assertions
html = HTML.read_text(encoding='utf-8')
src = APP.read_text(encoding='utf-8')
assert f'/static/coaching-v2.css?v={ASSET_VER}' in html
assert f'/static/coaching-v2.js?v={ASSET_VER}' in html
assert MARK in src
assert '("/static/coaching-v2.js","/static/coaching-v2.css")' in src
print('coaching cache invalidation patch: OK')
