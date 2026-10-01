"""Native ANA versus GENESIS integration on disposable full-image localhost only."""
import hashlib,http.cookiejar,json,os,sqlite3,sys,urllib.request,urllib.error
from pathlib import Path
BASE=os.environ.get('ANA_CANARY_URL','http://127.0.0.1:8000')
assert BASE in ('http://127.0.0.1:8000','http://127.0.0.1:18000'),'Disposable localhost only'
jar=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));csrf=''
def req(path,data=None,method=None,expect=200):
    headers={'Content-Type':'application/json','X-ANA-CSRF':csrf}
    request=urllib.request.Request(BASE+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    try:r=op.open(request,timeout=30)
    except urllib.error.HTTPError as e:r=e
    with r:
        raw=r.read();assert r.status==expect,(path,r.status,raw[:500])
        return json.loads(raw) if 'json' in r.headers.get('Content-Type','') else raw
req('/')
pool=req('/api/internal/question-studio-fingerprint')['sha256']
restart='--restart' in sys.argv
if not restart:req('/api/auth/setup-admin',{'username':'ana-canary','password':'disposable-ana-password'})
auth=req('/api/ana-prg/auth/teacher-login',{'username':'ana-canary','password':'disposable-ana-password'})
csrf=auth['csrf']
if restart:
    fixture=json.loads(Path('/tmp/ana-canary-fixture.json').read_text())
    assert pool==fixture['pool']
    student=req('/api/ana-prg/students')['items'][0]
    assert student['id']==fixture['student_id'] and student['class_id']==fixture['class_id']
    cls={'id':fixture['class_id']}
    assert req('/api/ana-prg/system/health')['restored']
else:
    cls=req('/api/ana-prg/classes',{'name':'Disposable ANA'})
    student=req('/api/ana-prg/students',{'name':'Disposable student','code':'DISPOSABLE_ANA','pin':'5678','class_id':cls['id'],'courses':['TYT_MAT']})
assert req('/api/ana-prg/students')['total']==1
assert req('/api/ana-prg/system/health')['ok']
for route in ('','program','classes','homework','assignments','submissions','ai','whatsapp','mock-exams','reports','settings','system','student'):
    assert b'/ana-prg/ana.js' in req('/ana-prg'+('/'+route if route else ''))
req('/coaching',expect=410);req('/api/coaching/v3/classes',expect=410)
assert req('/api/internal/question-studio-fingerprint')['sha256']==pool,'ANA writes changed protected pool'
with sqlite3.connect('/app/ANA_RUNTIME/ana.db') as c:
    assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    assert not c.execute('PRAGMA foreign_key_check').fetchall()
    assert all(r[0].startswith('ana_') for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'"))
Path('/tmp/ana-canary-fixture.json').write_text(json.dumps({'class_id':cls['id'],'student_id':student['id'],'pool':pool}))
print('ANA_NATIVE_FULL_IMAGE_RESTART_PASS' if restart else 'ANA_NATIVE_FULL_IMAGE_AUTH_ROUTES_SQLITE_QUESTION_ISOLATION_PASS')
