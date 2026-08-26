from pathlib import Path

ROOT=Path('/tmp/yilbay090')
app=ROOT/'app/public/app.js'
server=ROOT/'app/server.js'

a=app.read_text(encoding='utf-8')
s=server.read_text(encoding='utf-8')

a=a.replace('0.8.2','0.9.0')
s=s.replace('0.8.2','0.9.0')

# Idempotent UI completion: show the Drive filename metadata convention to the user.
if 'DERS__KONU__SEVIYE__BASLIK.pdf' not in a:
    marker='<span class="muted">Salt-okunur bağlantı</span>'
    if marker not in a:
        raise SystemExit('Drive panel heading marker missing')
    helper='<span class="muted">Salt-okunur bağlantı · Dosya adı: DERS__KONU__SEVIYE__BASLIK.pdf</span>'
    a=a.replace(marker,helper,1)

frontend_required=[
    'id="drivePanel"',
    'window.connectGoogleDrive=',
    'window.disconnectGoogleDrive=',
    'window.indexGoogleDrive=',
    'driveClientId',
    'driveClientSecret',
    'driveFolderId',
    'DERS__KONU__SEVIYE__BASLIK.pdf',
]
backend_required=[
    'driveClientId:String(next.driveClientId||"").trim()',
    'driveClientSecret:String(next.driveClientSecret||"").trim()',
    'driveFolderId:String(next.driveFolderId||"").trim()',
    'driveRefreshToken:String(next.driveRefreshToken||"").trim()',
    'driveAccessToken:String(next.driveAccessToken||"").trim()',
    'mode:"oauth-readonly"',
    'https://www.googleapis.com/auth/drive.readonly',
    'function driveRedirectUri()',
    'async function driveRefreshAccessToken()',
    'function driveMetadataFromFile(file)',
    'async function driveListPdfIndex()',
    'async function handleDriveOauthStart(req,res)',
    'async function handleDriveOauthCallback(u,res)',
    'async function handleDriveIndex(req,res)',
    '/api/drive/status',
    '/api/drive/oauth/start',
    '/api/drive/oauth/callback',
    '/api/drive/index',
    '/api/drive/disconnect',
    'driveClientId:b.driveClientId==="__KEEP__"?old.driveClientId:b.driveClientId',
    'driveClientSecret:b.driveClientSecret==="__KEEP__"?old.driveClientSecret:b.driveClientSecret',
    'driveFolderId:b.driveFolderId==="__KEEP__"?old.driveFolderId:b.driveFolderId',
]

missing_front=[x for x in frontend_required if x not in a]
missing_back=[x for x in backend_required if x not in s]
if missing_front:
    raise SystemExit('frontend Drive contract missing: '+', '.join(missing_front))
if missing_back:
    raise SystemExit('backend Drive contract missing: '+', '.join(missing_back))

app.write_text(a,encoding='utf-8')
server.write_text(s,encoding='utf-8')
(ROOT/'app/VERSION').write_text('0.9.0\n',encoding='utf-8')
print('v0.9.0 Drive contract verified; patch is idempotent')
