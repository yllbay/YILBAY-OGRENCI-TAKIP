"""Upgrade the live v1 guard: user-owned edits, with background protection retained."""
import ast
import os
from pathlib import Path

root = Path(os.getenv('GENESIS_CONTAINER_ROOT', '/app'))
backend = root / 'APP/backend'
app_path = backend / 'app.py'
app = app_path.read_text(encoding='utf-8')
MARKER = 'GENESIS_QUESTION_POOL_USER_OWNED_V2'
if MARKER in app:
    raise SystemExit(0)
assert 'GENESIS_QUESTION_POOL_APPEND_ONLY_V1' in app, 'Protected live base required'


def replace_function(source, name, replacement):
    node = next(node for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1:node.end_lineno] = [replacement.rstrip() + '\n']
    return ''.join(lines)


app = app.replace('import question_pool_policy\n', 'import question_pool_policy\nimport asyncio\n_pool_user_request_lock=asyncio.Lock()\n', 1)
app = replace_function(app, 'genesis_runtime_persist', '''
async def genesis_runtime_persist(request,call_next):
    method=request.method.upper();path=request.url.path
    explicit=question_pool_policy.question_write_route(method,path)
    if question_pool_policy.locked_route(method,path):
        return JSONResponse({"detail":"Otomatik soru temizliği kapalı.","code":"QUESTION_POOL_USER_ACTION_REQUIRED"},status_code=423)
    scope=None
    if explicit:
        cookie=request.cookies.get('genesis_session','')
        supplied=request.headers.get('x-genesis-user-intent','')
        session=await run_in_threadpool(session_from_token,cookie)
        if (not session or session.get('role') not in {'ADMIN','INSTITUTION'}
            or request.headers.get('sec-fetch-site')=='cross-site'
            or not question_pool_policy.valid_intent(cookie,supplied)):
            return JSONResponse({"detail":"Bu işlem için açık kullanıcı isteği gerekli. Sayfayı yenileyip tekrar deneyin.",
                                 "code":"QUESTION_POOL_USER_ACTION_REQUIRED"},status_code=403)
        scope={'actor':hashlib.sha256(cookie.encode()).hexdigest()[:24],
               'user_intent':True,'path':method+' '+path}
        await _pool_user_request_lock.acquire()
        runtime_storage.user_request_started()
    token=question_pool_policy.WRITE_SCOPE.set(scope)
    try:
        response=await call_next(request)
        if method in {'POST','PUT','PATCH','DELETE'} and response.status_code<400:
            try:
                await run_in_threadpool(runtime_storage.sync_once,pool_write=explicit)
            except Exception as error:
                runtime_storage.persistence_failed(error)
                return JSONResponse({"detail":"İşlem merkezi depoya aktarılmayı bekliyor. Eşitleme tamamlanmadan başarı verilmedi.",
                                     "code":"POOL_PERSISTENCE_PENDING"},status_code=503)
        if path.startswith('/api/'):
            response.headers['Cache-Control']='no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma']='no-cache'
        return response
    finally:
        question_pool_policy.WRITE_SCOPE.reset(token)
        if explicit:
            runtime_storage.user_request_finished()
            _pool_user_request_lock.release()
''')
# Deleting a question is deliberate. Coordinates and image references are removed in
# the same transaction; files are removed by storage only after the R2 DB commit.
app = replace_function(app, 'question_delete', '''
def question_delete(question_id:int):
    with connect() as con:
        q=con.execute('select * from questions where id=?',(question_id,)).fetchone()
        if not q:raise HTTPException(404,'Soru bulunamadı.')
        used=con.execute('select count(*) from exam_questions where question_id=?',(question_id,)).fetchone()[0]
        if used:raise HTTPException(409,f'Soru {used} sınavda kullanılıyor. Önce sınavlardan çıkarın.')
        crop_id=q['crop_session_id']
        drive_id=q['drive_file_id']
        if con.execute("select 1 from sqlite_master where name='question_asset_replication'").fetchone():
            replica=con.execute('select result_json from question_asset_replication where question_id=?',(question_id,)).fetchone()
            if replica:drive_id=json.loads(replica[0] or '{}').get('file_id') or drive_id
        paths=[str(q['raw_crop_path']),str(q['display_image_path'])]
        con.execute('delete from questions where id=?',(question_id,))
        if crop_id and not con.execute('select 1 from questions where crop_session_id=?',(crop_id,)).fetchone():
            con.execute('delete from crop_sessions where id=?',(crop_id,))
    drive=drive_delete_file(drive_id)
    audit('USER_DELETE','question',question_id,'Explicit user deletion; central commit required')
    log_event('question_deleted_by_user',f'id={question_id}')
    return {'ok':True,'question_id':question_id,'local_deleted':paths,
            'drive':drive,'drive_pending':drive.get('status') not in {'PURGED','NOT_PRESENT'}}
''')
# Empty folder deletion can remove its orphan drafts. Do not unlink files before
# the SQLite transaction and authoritative R2 snapshot have succeeded.
old = '''            for key in ("raw_crop_path","display_image_path"):
                rel=str(c.get(key) or "")
                if rel:
                    try:abs_data(rel).unlink(missing_ok=True)
                    except Exception:pass
            con.execute("delete from crop_sessions where id=?",(c["id"],))'''
assert old in app
app = app.replace(old, '''            con.execute("delete from crop_sessions where id=?",(c["id"],))''', 1)
app += '''

# GENESIS_QUESTION_POOL_USER_OWNED_V2
@app.get('/api/question-pool/user-token')
def genesis_question_pool_user_token(request:Request):
    cookie=request.cookies.get('genesis_session','')
    session=session_from_token(cookie) if cookie else None
    if not session or session.get('role') not in {'ADMIN','INSTITUTION'}:
        raise HTTPException(401,'Kullanıcı oturumu gerekli.')
    return {'token':question_pool_policy.intent_token(cookie)}
'''
ast.parse(app)
app_path.write_text(app, encoding='utf-8')

frontend = root / 'APP/frontend/dist/app-0.10.7.js'
js = frontend.read_text(encoding='utf-8')
js = js.replace('draggable="false"', 'draggable="${selecting?"false":"true"}"', 1)
js = js.replace('<span class="q-icon-btn" title="Kayıtlı soru korunuyor">🔒</span>',
                '<button class="q-icon-btn" data-qdelete="${q.id}" title="Sil">🗑</button>')
js = js.replace('data-qact="deleteall" class="danger" disabled title="Kayıtlı sorular korunuyor"',
                'data-qact="deleteall" class="danger"')
js = js.replace(' disabled title="Kayıtlı klasör korunuyor"', '')
js = js.replace('disabled title="Kayıtlı soru korunuyor" data-boutcome=', 'data-boutcome=')
js = js.replace('S.dragArmed=false;el.draggable=false;', 'S.dragArmed=true;el.draggable=true;')
js = js.replace('S.testDragArmed=false;S.testDrag=null;el.draggable=false;',
                'S.testDragArmed=true;S.testDrag={type:"class",id:cid};el.draggable=true;')
js = js.replace('Bu soru silinsin mi? Ham kesim, kayıtlı görsel, yerel yedek kopyaları ve Drive snapshot kopyaları da silinecek.',
                'Bu soru ve kayıtlı kesim görselleri kalıcı olarak silinsin mi?')
# Tokens are bound to the existing authenticated cookie. Only deliberate pool APIs
# use them. Background refresh/sound/coaching requests never get this capability.
anchor = ' const r=await fetch(u,{...o,cache:"no-store"});'
assert anchor in js
js = js.replace(anchor, ''' const method=(o?.method||"GET").toUpperCase();
 const path=String(u).split("?")[0];
 const isPoolWrite=["POST","PUT","PATCH","DELETE"].includes(method)&&
   /^\\/api\\/(topics(?:\\/\\d+(?:\\/move)?)?|sources\\/upload|sources\\/\\d+\\/release|crops(?:\\/.*)?|questions\\/(?:delete-all|\\d+(?:\\/(?:move|learning-outcome))?)|answerkey\\/(?:analyze|ai-analyze)|classes(?:\\/\\d+(?:\\/move)?)?|exams(?:\\/.*)?|screen-capture(?:\\/.*)?|windows-capture(?:\\/.*)?|windows-overlay(?:\\/.*)?)$/.test(path);
 let options={...o,cache:"no-store"};
 if(isPoolWrite){
   const auth=await fetch("/api/question-pool/user-token",{cache:"no-store"});
   if(!auth.ok)throw new Error("Kullanıcı oturumu yenilenemedi. Sayfayı yenileyin.");
   const permit=await auth.json();
   const headers=new Headers(o?.headers||{});
   headers.set("X-Genesis-User-Intent",permit.token);
   options.headers=headers;
 }
 const r=await fetch(u,options);''', 1)
js += '\n// GENESIS_QUESTION_POOL_USER_OWNED_V2: explicit user edits; no automatic destructive writes.\n'
frontend.write_text(js, encoding='utf-8')
index_path = root / 'APP/frontend/dist/index.html'
index = index_path.read_text(encoding='utf-8').replace('pool-append-only-20261001','pool-user-owned-20261001')
index_path.write_text(index, encoding='utf-8')
print(MARKER, 'user controls and transactional audit enabled; automatic cleanup remains retired')
