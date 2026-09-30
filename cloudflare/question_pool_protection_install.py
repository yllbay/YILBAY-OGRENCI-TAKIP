"""Install pool protection into the exact currently deployed application."""
import ast
import os
from pathlib import Path

root = Path(os.getenv('GENESIS_CONTAINER_ROOT', '/app'))
backend = root / 'APP/backend'
app_path = backend / 'app.py'
db_path = backend / 'db.py'
app = app_path.read_text(encoding='utf-8')
db = db_path.read_text(encoding='utf-8')
MARKER = 'GENESIS_QUESTION_POOL_APPEND_ONLY_V1'
if MARKER in app:
    raise SystemExit(0)


def replace_function(source, name, replacement):
    node = next(node for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1:node.end_lineno] = [replacement.rstrip() + '\n']
    return ''.join(lines)


db = db.replace('import contextvars', 'import contextvars\nimport question_pool_policy\nquestion_pool_policy.enable()', 1)
# Existing folder names/order are user data, not a startup formatting migration.
db = db.replace('        _normalize_hierarchical_folder_names(con,"topics")',
                '        # Existing topics are immutable; format only new user-created folders.')
db = db.replace('        _normalize_hierarchical_folder_names(con,"test_classes")',
                '        # Existing test folders are never normalized on startup.')
db = db.replace('        con.commit()\n\n@contextmanager',
                '        question_pool_policy.install_triggers(con)\n        con.commit()\n\n@contextmanager', 1)
assert 'question_pool_policy.install_triggers(con)' in db
db_path.write_text(db, encoding='utf-8')

app = app.replace('import runtime_storage', 'import runtime_storage\nimport question_pool_policy', 1)
app = app.replace('\ninit_db()\n', '''
_pool_schema_token=question_pool_policy.SCHEMA_SCOPE.set(True)
try:
    init_db()
finally:
    question_pool_policy.SCHEMA_SCOPE.reset(_pool_schema_token)
''', 1)
# Retire all automatic deletion paths, including runtime cleanup called by upload/finalize.
for name in ('purge_pending_deletions_on_startup', 'purge_stale_prepared_on_startup',
             'purge_finalized_working_files_on_startup', 'purge_transient_source_files_on_startup',
             '_purge_historical_finalized_working_files', '_cleanup_transient_sources',
             '_stale_prepared_cleanup'):
    app = replace_function(app, name, f'def {name}(*args,**kwargs):\n    return {{"protected":True,"purged":False}}')
app = replace_function(app, '_purge_finalized_raw', '''
def _purge_finalized_raw(question_id:int,crop_id:int,raw_rel:str,display_rel:str):
    return {"protected":True,"purged":False,"reason":"question_pool_immutable"}
''')
app = replace_function(app, '_purge_source_payload', '''
def _purge_source_payload(source_id:int,reason:str,force=False):
    return {"protected":True,"purged":False,"reason":"question_pool_immutable"}
''')
app = replace_function(app, '_maybe_purge_windows_source', '''
def _maybe_purge_windows_source(source_id:int):
    return {"protected":True,"purged":False,"reason":"question_pool_immutable"}
''')
app = replace_function(app, '_touch_source', 'def _touch_source(source_id:int):\n    return None')
app = replace_function(app, '_normalize_classes', 'def _normalize_classes(con,parent_id):\n    return None')
app = replace_function(app, 'genesis_runtime_storage_start', '''
def genesis_runtime_storage_start():
    runtime_storage.start()
''')
# Source PDFs must survive restart too. New sources are stored under DATA/Sources.
app = app.replace('    upload_root=TRANSIENT_PDF if is_pdf else SOURCES', '    upload_root=SOURCES')
app = app.replace('            path=TRANSIENT_PDF/f"{digest}{ext}"\n            stored=str(path)',
                  '            stored=f"Sources/{digest}{ext}"\n            path=DATA/stored')
app = app.replace('"TRANSIENT_PDF" if is_pdf else "STANDARD"', '"SOURCE_MASTER"')
app = app.replace('                    con.execute("update source_documents set last_accessed_at=CURRENT_TIMESTAMP where id=?",(int(existing["id"]),))',
                  '                    # Existing source metadata is immutable.')
# Answer keys may populate drafts, but must not rewrite answers in saved questions.
app = app.replace('                con.execute("update questions set answer=?,updated_at=CURRENT_TIMESTAMP where id=?",(e.answer,qid))',
                  '                pass  # Saved question answers are immutable; draft processing continues.')

old_bbox = '''    bbox,outside,diag=_find_expected_number_on_pdf_page(row,int(expected))
    if outside:
        return {"masked":False,"reason":"number_outside_crop","diagnostics":diag}
    if bbox is None:
        # Fallback to exact-token OCR on the immutable raw crop.
        bbox,raw_diag=_exact_question_number_bbox(raw,int(expected))
        diag={"page":diag,"raw":raw_diag}
'''
new_bbox = '''    # Saved geometry wins; PDF page coordinates are explicitly converted to crop pixels.
    bbox=None;outside=False;diag={"method":"stored_crop_bbox"}
    try:
        saved=json.loads(row["source_number_bbox"] or '{}')
        if all(saved.get(key) is not None for key in ('x0','y0','x1','y1')):
            coords=[float(saved[key]) for key in ('x0','y0','x1','y1')]
            if saved.get('kind')=='pdf_or_ocr_page':
                src=source_row(int(row['source_id']))
                with fitz.open(_source_file(src)) as document:
                    page=document[int(row['page_no'])-1].rect
                    origin_x=page.x0+page.width*float(row['x0'])
                    origin_y=page.y0+page.height*float(row['y0'])
                    coords=[(coords[0]-origin_x)*2,(coords[1]-origin_y)*2,
                            (coords[2]-origin_x)*2,(coords[3]-origin_y)*2]
            with Image.open(raw) as image:
                if 0<=coords[0]<coords[2]<=image.width and 0<=coords[1]<coords[3]<=image.height:
                    bbox=tuple(int(round(value)) for value in coords)
    except Exception:
        bbox=None
    if bbox is None:
        bbox,outside,diag=_find_expected_number_on_pdf_page(row,int(expected))
        if outside:
            return {"masked":False,"reason":"number_outside_crop","diagnostics":diag}
        if bbox is None:
            bbox,raw_diag=_exact_question_number_bbox(raw,int(expected))
            diag={"page":diag,"raw":raw_diag}
'''
assert old_bbox in app
app = app.replace(old_bbox, new_bbox, 1)

# Replication metadata belongs outside the immutable question record.
old = '''    with connect() as con:
        if status=="SYNCED":
            con.execute("""update questions set drive_file_id=?,drive_parent_id=?,drive_path=?,
                           drive_status='SYNCED',drive_error=null,drive_synced_at=CURRENT_TIMESTAMP,
                           updated_at=CURRENT_TIMESTAMP where id=?""",
                        (result.get("file_id"),result.get("parent_id"),result.get("path"),int(question_id)))
        else:
            con.execute("update questions set drive_status=?,drive_error=?,updated_at=CURRENT_TIMESTAMP where id=?",
                        (status,str(result.get("detail") or "")[:500],int(question_id)))
'''
new = '''    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS question_asset_replication(
            question_id INTEGER PRIMARY KEY, status TEXT, result_json TEXT, updated_at TEXT)""")
        con.execute("""INSERT INTO question_asset_replication VALUES(?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(question_id) DO UPDATE SET status=excluded.status,
            result_json=excluded.result_json,updated_at=excluded.updated_at""",
            (int(question_id),status,json.dumps(result,ensure_ascii=False)))
'''
assert old in app, 'Drive metadata update anchor changed'
app = app.replace(old, new, 1)
# Reuse the existing Drive copy on later retries, without rewriting question metadata.
anchor = '    by_id={int(x["id"]):x for x in topic_rows}\n    topic_path=_topic_path(by_id,int(row["topic_id"]))'
replacement = '''    row=dict(row)
    with connect() as con:
        if con.execute("select 1 from sqlite_master where name='question_asset_replication'").fetchone():
            replica=con.execute("select result_json from question_asset_replication where question_id=?",(question_id,)).fetchone()
            if replica:
                saved=json.loads(replica[0] or '{}')
                row['drive_file_id']=saved.get('file_id') or row.get('drive_file_id')
                row['drive_parent_id']=saved.get('parent_id') or row.get('drive_parent_id')
    by_id={int(x["id"]):x for x in topic_rows}
    topic_path=_topic_path(by_id,int(row["topic_id"]))'''
assert anchor in app
app = app.replace(anchor, replacement, 1)

app = replace_function(app, 'genesis_runtime_persist', '''
async def genesis_runtime_persist(request,call_next):
    method=request.method.upper();path=request.url.path
    if question_pool_policy.locked_route(method,path):
        return JSONResponse({"detail":"Kayıtlı soru ve klasörler korunuyor; silme ve değiştirme kapalı.",
                             "code":"QUESTION_POOL_IMMUTABLE"},status_code=423)
    explicit=question_pool_policy.question_write_route(method,path)
    scope={"new_rows":{},"path":path} if explicit else None
    token=question_pool_policy.WRITE_SCOPE.set(scope)
    try:
        response=await call_next(request)
        if method in {"POST","PUT","PATCH","DELETE"} and response.status_code<400:
            try:
                await run_in_threadpool(runtime_storage.sync_once,pool_write=explicit)
            except Exception:
                return JSONResponse({"detail":"Kayıt merkezi depoya aktarılmadı. Veriler korunuyor; tekrar denemeden önce eşitlemenin tamamlanmasını bekleyin.",
                                     "code":"POOL_PERSISTENCE_PENDING"},status_code=503)
        if path.startswith('/api/'):
            response.headers['Cache-Control']='no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma']='no-cache'
        return response
    finally:
        question_pool_policy.WRITE_SCOPE.reset(token)
''')
app += '''

# GENESIS_QUESTION_POOL_APPEND_ONLY_V1
@app.get('/api/internal/question-studio-fingerprint')
def genesis_question_pool_fingerprint():
    with connect(DB) as con:
        return question_pool_policy.fingerprint(con)

@app.get('/api/question-pool/revision')
def genesis_question_pool_revision():
    return runtime_storage.pool_status()
'''
ast.parse(app)
app_path.write_text(app, encoding='utf-8')

frontend = root / 'APP/frontend/dist/app-0.10.7.js'
js = frontend.read_text(encoding='utf-8')
js = js.replace(' const r=await fetch(u,o);', ' const r=await fetch(u,{...o,cache:"no-store"});', 1)
js = js.replace('   api("/api/test-tree").catch(()=>[])', '   api("/api/test-tree")', 1)
js = js.replace(' }catch{S.questions=[]}', ' }catch(error){throw error}', 1)
js = js.replace('draggable="${selecting?"false":"true"}"', 'draggable="false"')
js = js.replace('<button class="q-icon-btn" data-qdelete="${q.id}" title="Sil">🗑</button>',
                '<span class="q-icon-btn" title="Kayıtlı soru korunuyor">🔒</span>')
js = js.replace('data-qact="deleteall" class="danger"', 'data-qact="deleteall" class="danger" disabled title="Kayıtlı sorular korunuyor"')
for action in ('update', 'delete', 'toroot'):
    js = js.replace(f'<button data-act="{action}"',
                    f'<button disabled title="Kayıtlı klasör korunuyor" data-act="{action}"')
js = js.replace('S.dragArmed=true;el.draggable=true;', 'S.dragArmed=false;el.draggable=false;')
js = js.replace('S.testDragArmed=true;S.testDrag={type:"class",id:cid};el.draggable=true;',
                'S.testDragArmed=false;S.testDrag=null;el.draggable=false;')
for action in ('deleteclass', 'toroot'):
    js = js.replace(f'<button data-exam-act="{action}"',
                    f'<button disabled title="Kayıtlı klasör korunuyor" data-exam-act="{action}"')
js = js.replace('data-boutcome="${q.id}"', 'disabled title="Kayıtlı soru korunuyor" data-boutcome="${q.id}"')
# Premium CSS defines pane width/flex with !important; ordinary inline styles
# never moved the splitter. User drag must take precedence over initial ratios.
old_split = '''    l.style.width=nl+"px";l.style.flex="none";
    r.style.width=nr+"px";r.style.flex="none";'''
new_split = '''    l.style.setProperty("width",nl+"px","important");l.style.setProperty("flex","none","important");
    r.style.setProperty("width",nr+"px","important");r.style.setProperty("flex","none","important");'''
assert old_split in js
js = js.replace(old_split, new_split, 1)
js += '''

// GENESIS_QUESTION_POOL_APPEND_ONLY_V1: server revision, never a browser-owned pool.
let genesisPoolRevision=null, genesisPoolRefreshBusy=false;
async function genesisRefreshCentralPool(){
  if(genesisPoolRefreshBusy||document.hidden)return;
  genesisPoolRefreshBusy=true;
  try{
    const state=await api('/api/question-pool/revision');
    if(!state.durable||state.pending||!state.revision)return;
    if(genesisPoolRevision===null){genesisPoolRevision=state.revision;return;}
    if(genesisPoolRevision!==state.revision){
      if(S.editor||S.builder||S.candidate||S.page)return;
      await refresh();
      genesisPoolRevision=state.revision;
    }
  }catch(error){console.warn('Soru havuzu yenilemesi bekliyor:',error.message)}
  finally{genesisPoolRefreshBusy=false;}
}
setInterval(genesisRefreshCentralPool,5000);
addEventListener('focus',genesisRefreshCentralPool);
addEventListener('pageshow',genesisRefreshCentralPool);
document.addEventListener('visibilitychange',genesisRefreshCentralPool);
genesisRefreshCentralPool();
'''
frontend.write_text(js, encoding='utf-8')
css_path = root / 'APP/frontend/dist/genesis-premium-0.11.7.css'
with css_path.open('a', encoding='utf-8') as stream:
    stream.write('''
/* GENESIS_QUESTION_POOL_APPEND_ONLY_V1 */
.genesis #workspace{overflow-x:hidden!important;min-width:0!important}
.genesis #workspace>.pane{min-width:0!important;overflow:hidden}
.genesis #workspace>.splitter{width:16px!important;min-width:16px!important;max-width:16px!important;flex:0 0 16px!important;cursor:col-resize!important;touch-action:none}
''')
print(MARKER, 'automatic cleanup retired; immutable pool and central revision installed')
