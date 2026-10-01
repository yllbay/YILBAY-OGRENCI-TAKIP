"""HTTP APIs and server-side authorization for native ANA PRG."""
from __future__ import annotations
import csv, hashlib, hmac, io, json, os, sqlite3, threading, time
from pathlib import Path
from urllib.parse import urlparse
from fastapi import APIRouter,Request,HTTPException,UploadFile,File,Form
from fastapi.responses import JSONResponse,Response,FileResponse
from .storage import Store,LocalObjects,TABLES,encode,now
from .service import Service
from .domain import COURSES,FORMATS,monday,item_analysis,safe_csv_cell

BASE='/api/ana-prg'
CRUD={'classes':'classes','students':'students','homework':'homework_pool','assignments':'assignments',
      'guardians':'guardians','templates':'whatsapp_templates','course-rules':'course_rules','videos':'videos',
      'topic-order':'topic_order','ai-references':'ai_references','mock-exams':'mock_exams'}
LIST={'submissions':'submissions','answer-keys':'answer_keys','evaluations':'ai_evaluations','ai/queue':'ai_queue',
      'whatsapp/queue':'whatsapp_queue','files':'files','mock-optics':'mock_optics','mock-results':'mock_results',
      'costs':'costs','weekly-reports':'weekly_reports','programs':'programs','program-slots':'program_slots'}

def install(app,dist,service=None,teacher_verify=None,genesis_session=None):
    if service is None:
        local=os.environ.get('GENESIS_STORAGE_MODE')=='local'
        root=os.environ.get('ANA_RUNTIME_ROOT','/app/ANA_RUNTIME')
        objects=LocalObjects(Path(root)/'objects') if local else None
        service=Service(Store(root,objects))
    s=service;app.state.ana_prg=s;router=APIRouter(prefix=BASE)
    if teacher_verify is None:
        def teacher_verify(username,password):
            from db import DB,connect
            from auth import verify_password,create_session
            with connect(DB) as c:r=c.execute('SELECT * FROM genesis_admin WHERE id=1').fetchone()
            if r and hmac.compare_digest(str(r['username']),str(username).strip()) and verify_password(password,r['salt']+':'+r['password_hash']):
                return create_session('ADMIN')
            return None
    if genesis_session is None:
        from auth import session_from_token
        genesis_session=session_from_token

    def require(request,student=False):
        session=s.get_session(request.cookies.get('ana_session'))
        if not session:raise HTTPException(401,'ANA PRG oturumu gerekli.')
        if student:
            if session['role']!='STUDENT':raise HTTPException(403,'Öğrenci oturumu gerekli.')
        else:
            gs=genesis_session(request.cookies.get('genesis_session'))
            if session['role']!='ADMIN' or not gs or gs.get('role')!='ADMIN' or gs.get('institution_id'):
                raise HTTPException(403,'Doğrulanmış GENESIS öğretmen oturumu gerekli.')
        if request.method not in ('GET','HEAD','OPTIONS'):
            csrf=request.headers.get('x-ana-csrf','')
            if not hmac.compare_digest(csrf,session['csrf']):raise HTTPException(403,'CSRF doğrulaması başarısız.')
        return session

    def origin(request):
        value=request.headers.get('origin')
        allowed={request.url.hostname,'genesis-web-0152.yilbayonurcelik.workers.dev','localhost','127.0.0.1'}
        if value and (urlparse(value).scheme not in ('https','http') or urlparse(value).hostname not in allowed):
            raise HTTPException(403,'İstek kaynağı kabul edilmedi.')

    @app.middleware('http')
    async def ana_boundary(request,call_next):
        p=request.url.path
        if p.startswith('/coaching') or p.startswith('/api/coaching') or p.startswith('/static/coaching-'):
            return JSONResponse({'detail':'Koçluk modülü kaldırıldı. ANA PRG /ana-prg adresinde.'},410)
        if p.startswith(BASE) or p.startswith('/ana-prg'):
            if request.method not in ('GET','HEAD','OPTIONS'):
                try:origin(request)
                except HTTPException as e:return JSONResponse({'detail':e.detail},e.status_code)
                if int(request.headers.get('content-length','0') or 0)>21*1024*1024:
                    return JSONResponse({'detail':'İstek boyutu sınırı aşıldı.'},413)
            try:response=await call_next(request)
            except (ValueError,sqlite3.IntegrityError) as e:
                message=str(e) if isinstance(e,ValueError) else 'Kayıt kodu zaten kullanılıyor veya ilişki geçersiz.'
                response=JSONResponse({'detail':message},400)
            except Exception as e:
                # Do not leak provider credentials, SQL, PINs, request bodies.
                response=JSONResponse({'detail':'İşlem tamamlanamadı. Sistem durumunu kontrol edin.','code':type(e).__name__},503)
            response.headers['Cache-Control']='no-store'
            response.headers['X-Content-Type-Options']='nosniff'
            response.headers['Referrer-Policy']='same-origin'
            return response
        return await call_next(request)

    def login_response(request,result,genesis_token=None):
        response=JSONResponse({k:v for k,v in result.items() if k!='token'})
        secure=request.url.scheme=='https' or request.headers.get('x-forwarded-proto')=='https'
        response.set_cookie('ana_session',result['token'],max_age=3600 if result['role']=='STUDENT' else 8*3600,
            path=BASE,httponly=True,secure=secure,samesite='strict')
        if genesis_token:response.set_cookie('genesis_session',genesis_token,max_age=30*86400,path='/',httponly=True,secure=secure,samesite='lax')
        return response

    @router.post('/auth/teacher-login')
    def teacher_login(request:Request,body:dict):
        key='teacher:'+hashlib.sha256((request.client.host if request.client else '').encode()).hexdigest()
        with s.store.transaction('anonymous','teacher-login-limit') as c:s.rate_limit(c,key,10,900)
        token=teacher_verify(str(body.get('username',''))[:80],str(body.get('password',''))[:200])
        if not token:raise HTTPException(401,'GENESIS öğretmen kullanıcı adı/şifresi hatalı.')
        with s.store.transaction('ADMIN','teacher-login') as c:result=s.session(c,'ADMIN')
        return login_response(request,result,token)

    @router.post('/student/auth/login')
    def student_login(request:Request,body:dict):
        result=s.student_login(str(body.get('code',''))[:80],str(body.get('pin',''))[:100],request.client.host if request.client else '')
        return login_response(request,result)

    @router.get('/auth/me')
    def auth_me(request:Request):
        session=s.get_session(request.cookies.get('ana_session'))
        if session and session['role']=='ADMIN':
            gs=genesis_session(request.cookies.get('genesis_session'))
            if not gs or gs.get('role')!='ADMIN':session=None
        if not session:return dict(authenticated=False)
        return dict(authenticated=True,role=session['role'],student_id=session.get('student_id'),csrf=session['csrf'],expires_at=session['expires_at'])

    @router.post('/auth/logout')
    def logout(request:Request):
        session=s.get_session(request.cookies.get('ana_session'))
        if session:
            if not hmac.compare_digest(request.headers.get('x-ana-csrf',''),session['csrf']):raise HTTPException(403,'CSRF gerekli.')
            with s.store.transaction(session['role'],'logout') as c:c.execute('DELETE FROM ana_sessions WHERE token_hash=?',(session['token_hash'],))
        response=JSONResponse({'ok':True});response.delete_cookie('ana_session',path=BASE);return response

    @router.get('/catalog')
    def catalog(request:Request):
        session=s.get_session(request.cookies.get('ana_session'))
        if not session:raise HTTPException(401,'Oturum gerekli.')
        return dict(courses=COURSES,formats={k:dict(label=v['label'],subjects=[dict(code=c,label=l,q=q,w=w) for c,l,q,w in v['subjects']]) for k,v in FORMATS.items()})

    @router.get('/dashboard')
    def dashboard(request:Request):require(request);return s.dashboard()

    def add_crud(path,table):
        def listing(request:Request,limit:int=100,offset:int=0,search:str='',student_id:str='',course:str='',week:str='',status:str='',archived:bool=False):
            require(request);limit=max(1,min(500,limit));offset=max(0,offset);clauses=['active=?'];args=[0 if archived else 1]
            for k,v in [('student_id',student_id),('course',course),('week',week),('status',status)]:
                if v:clauses.append(k+'=?');args.append(v)
            if search:clauses.append("data LIKE ? ESCAPE '\\'");args.append('%'+search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')[:150]+'%')
            where=' AND '.join(clauses)
            with s.store.connect() as c:
                total=c.execute(f'SELECT count(*) FROM ana_{table} WHERE '+where,tuple(args)).fetchone()[0]
                rows=s.store.rows(table,c,where=where,args=tuple(args),limit=limit,offset=offset)
            return dict(items=[s.public(table,r) for r in rows],total=total,limit=limit,offset=offset)
        listing.__name__='list_'+table
        router.add_api_route('/'+path,listing,methods=['GET'])
        if path not in CRUD:return
        def create(request:Request,body:dict):require(request);return s.save(table,body,'ADMIN')
        def update(id:str,request:Request,body:dict):require(request);return s.save(table,body,'ADMIN',id)
        def archive(id:str,request:Request):require(request);return s.archive(table,id,'ADMIN')
        router.add_api_route('/'+path,create,methods=['POST'])
        router.add_api_route('/'+path+'/{id}',update,methods=['PATCH'])
        router.add_api_route('/'+path+'/{id}',archive,methods=['DELETE'])
    for path,table in {**CRUD,**LIST}.items():add_crud(path,table)

    @router.post('/files/upload')
    async def upload(request:Request,file:UploadFile=File(...),category:str=Form('homework'),student_id:str=Form('')):
        session=s.get_session(request.cookies.get('ana_session'))
        if not session:raise HTTPException(401,'Oturum gerekli.')
        require(request,student=session['role']=='STUDENT')
        if session['role']=='STUDENT':
            category='submissions';student_id=session['student_id']
        elif student_id:s.store.get('students',student_id)
        # Bound reads even when Content-Length is absent/chunked.
        parts=[];size=0
        while chunk:=await file.read(1024*1024):
            size+=len(chunk)
            if size>20*1024*1024:raise HTTPException(413,'Dosya en fazla 20 MB olabilir.')
            parts.append(chunk)
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(s.upload,file.filename,file.content_type,b''.join(parts),session['role'],student_id or None,category)

    @router.get('/files/{id}/content')
    def file_content(id:str,request:Request):
        session=s.get_session(request.cookies.get('ana_session'))
        if not session:raise HTTPException(401,'Oturum gerekli.')
        require(request,student=session['role']=='STUDENT');file=s.store.get('files',id)
        if session['role']=='STUDENT':
            sid=session['student_id'];allowed=file.get('student_id')==sid
            if file.get('category')=='homework':
                with s.store.connect() as c:
                    allowed=bool(c.execute('''SELECT 1 FROM ana_assignments a JOIN ana_homework_pool h ON h.id=a.homework_id
                        WHERE a.student_id=? AND a.active=1 AND h.file_id=? LIMIT 1''',(sid,id)).fetchone())
            if not allowed:raise HTTPException(403,'Bu dosyaya erişim yetkiniz yok.')
        data,_=s.store.objects.get(file['key'])
        if not data or hashlib.sha256(data).hexdigest()!=file['sha256']:raise HTTPException(503,'Dosya bütünlüğü doğrulanamadı.')
        from urllib.parse import quote
        return Response(data,media_type=file['mime'],headers={'Content-Disposition':"inline; filename*=UTF-8''"+quote(file['name']),'X-ANA-SHA256':file['sha256']})

    @router.post('/programs/generate')
    def generate(request:Request,body:dict):require(request);return s.generate(body,'ADMIN',body.get('preview',False))
    @router.post('/programs/sync')
    def sync(request:Request,body:dict):
        require(request);week=monday(body['week']).isoformat()
        with s.store.transaction('ADMIN','sync-program',week) as c:count=s.sync(week,c)
        return dict(ok=True,created=count)
    @router.post('/programs/reset')
    def reset(request:Request,body:dict):require(request);return s.reset_week(body['week'],'ADMIN')
    @router.post('/programs/next-week')
    def next_week(request:Request,body:dict):
        import datetime
        require(request);week=(monday(body['week'])+datetime.timedelta(days=7)).isoformat()
        return s.generate(dict(week=week,skip_past=True),'ADMIN')
    @router.post('/programs/slot')
    def manual_slot(request:Request,body:dict):require(request);return s.manual_slot(body,'ADMIN')

    @router.post('/submissions')
    def submit(request:Request,body:dict):
        session=s.get_session(request.cookies.get('ana_session'))
        if not session:raise HTTPException(401,'Oturum gerekli.')
        require(request,student=session['role']=='STUDENT')
        sid=session['student_id'] if session['role']=='STUDENT' else body['student_id']
        return s.submit(body,session['role'],sid)

    @router.post('/homework/{id}/answer-key')
    def homework_key(id:str,request:Request,body:dict):require(request);return s.approve_key(id,body['answers'],'ADMIN')

    @router.post('/ai/queue')
    def queue_ai(request:Request,body:dict):require(request);return s.queue_ai(body,'ADMIN')
    @router.post('/ai/queue/{id}/retry')
    def retry_ai(id:str,request:Request,body:dict):require(request);return s.retry_job(id,'ADMIN',body.get('confirmed',False))
    @router.post('/ai/run')
    def run_ai(request:Request,body:dict):
        require(request);s.require_live()
        limit=max(1,min(10,int(body.get('limit',3))))
        def run():
            try:s.process_jobs(limit)
            except Exception:pass # Detailed per-job errors are durable; do not print secret-bearing exceptions.
        threading.Thread(target=run,daemon=True).start()
        return dict(ok=True,accepted=True,message='İşler arka planda işleniyor; kuyruk durumunu yenileyin.')
    @router.post('/evaluations/{id}/approve')
    def approve_evaluation(id:str,request:Request):
        require(request)
        with s.store.transaction('ADMIN','approve-evaluation',id) as c:
            item=s.store.get('ai_evaluations',id,c);item=s.store.put('ai_evaluations',{**item,'status':'APPROVED','approved_at':now()},c)
            sub=s.store.get('submissions',item['submission_id'],c);s.store.put('submissions',{**sub,'status':'APPROVED'},c)
        return item

    @router.post('/evaluations/{id}/review')
    def review_evaluation(id:str,request:Request,body:dict):
        require(request)
        with s.store.transaction('ADMIN','correct-evaluation',id) as c:
            item=s.store.get('ai_evaluations',id,c);homework=s.store.get('homework_pool',item['homework_id'],c)
            answers=body.get('answers')
            if not isinstance(answers,list) or len(answers)!=homework['questions']:raise ValueError('Düzeltme soru sayısı uyuşmuyor.')
            answers=[str(a).strip().upper() for a in answers]
            if any(a not in ('A','B','C','D','E','') for a in answers):raise ValueError('Cevaplar A–E veya boş olmalı.')
            keys=s.store.rows('answer_keys',c,where="homework_id=? AND status='APPROVED' AND active=1",args=(homework['id'],),limit=1)
            if not keys:raise ValueError('Onaylı ödev anahtarı gerekli.')
            key=keys[0]['answers'];correct=sum(bool(a) and a==b for a,b in zip(answers,key));blank=answers.count('');wrong=len(answers)-correct-blank
            result=s.store.put('ai_evaluations',{**item,'answers':answers,'correct':correct,'wrong':wrong,'blank':blank,
                'net':correct-wrong/4,'status':'APPROVED','approved_at':now(),'manual_corrected':True},c)
            sub=s.store.get('submissions',item['submission_id'],c);s.store.put('submissions',{**sub,'status':'APPROVED'},c)
        return result

    @router.post('/mock-exams/{id}/answer-key')
    def save_key(id:str,request:Request,body:dict):require(request);return s.save_key(id,body['key'],'ADMIN')
    @router.get('/mock-exams/{id}/answer-key')
    def read_key(id:str,request:Request):require(request);exam=s.store.get('mock_exams',id);return dict(key=exam.get('key',{}),ai_key=exam.get('ai_key',{}),kind=exam['kind'])
    @router.post('/mock-exams/{id}/optics/whole')
    def whole_optical(id:str,request:Request,body:dict):require(request);return s.queue_ai({**body,'kind':'whole_optical','exam_id':id},'ADMIN')
    @router.post('/mock-exams/{id}/optics/batch')
    def batch_optical(id:str,request:Request,body:dict):
        require(request);items=body.get('items')
        if not isinstance(items,list) or not 1<=len(items)<=50:raise ValueError('Toplu optik 1–50 dosya eşlemesi içermeli.')
        result=[]
        for item in items:
            try:result.append(dict(student_id=item['student_id'],job=s.queue_ai({**item,'kind':'whole_optical','exam_id':id},'ADMIN')))
            except ValueError as e:result.append(dict(student_id=item.get('student_id'),error=str(e)))
        return dict(items=result)
    @router.post('/mock-optics/{id}/approve')
    def approve_optical(id:str,request:Request,body:dict):require(request);return s.review_optical(id,body['answers'],'ADMIN')
    @router.get('/mock-exams/{id}/results')
    def exam_results(id:str,request:Request):
        require(request);exam=s.store.get('mock_exams',id);results=s.store.rows('mock_results',where='exam_id=? AND active=1',args=(id,),limit=100000)
        optics=s.latest_optics(id)
        analysis=item_analysis(exam['kind'],exam['key'],optics,results) if exam.get('status')=='READY' else []
        leaderboard=sorted(results,key=lambda r:r['report']['totals']['net'],reverse=True)
        return dict(exam=exam,results=results,item_analysis=analysis,leaderboard=leaderboard,optics=optics)

    @router.post('/whatsapp/queue')
    def queue_whatsapp(request:Request,body:dict):require(request);return s.queue_whatsapp(body,'ADMIN')
    @router.post('/whatsapp/queue/{id}/send')
    def send_whatsapp(id:str,request:Request):require(request);return s.send_whatsapp(id,'ADMIN')
    @router.post('/whatsapp/queue/{id}/retry')
    def retry_whatsapp(id:str,request:Request):require(request);return s.retry_whatsapp(id,'ADMIN')

    @router.get('/reports')
    def report(request:Request,student_id:str='',week:str=''):require(request);return s.report(student_id or None,week or None)
    @router.post('/reports/snapshot')
    def report_snapshot(request:Request,body:dict):
        require(request);report=s.report(body.get('student_id'),body.get('week'))
        with s.store.transaction('ADMIN','weekly-report') as c:item=s.store.put('weekly_reports',dict(week=body.get('week'),student_id=body.get('student_id'),report=report,name='Haftalık rapor'),c)
        return item
    def csv_response(rows,name):
        out=io.StringIO(newline='');writer=csv.writer(out)
        writer.writerows([[safe_csv_cell(v) for v in row] for row in rows])
        return Response('\ufeff'+out.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename='+name})
    @router.get('/reports/export.csv')
    def report_csv(request:Request,student_id:str='',week:str=''):
        require(request);report=s.report(student_id or None,week or None)
        rows=[['Öğrenci','Atama','Teslim','Tamamlama %']]+[[r['name'],r['assigned'],r['submitted'],round(100*r['submitted']/r['assigned'],2) if r['assigned'] else 0] for r in report['students']]
        return csv_response(rows,'ANA_PRG_RAPOR.csv')
    @router.get('/mock-exams/{id}/export.csv')
    def exam_csv(id:str,request:Request):
        require(request);exam=s.store.get('mock_exams',id);results=s.store.rows('mock_results',where='exam_id=? AND active=1',args=(id,),limit=100000)
        subjects=FORMATS[exam['kind']]['subjects'];rows=[['Öğrenci','D','Y','B','Net','Demo puan','Demo sıra','2026 tahmini sıra','Onay']+[x[1]+' Net' for x in subjects]]
        for r in results:
            p=r['report'];rows.append([p['student']['name'],*[p['totals'][k] for k in ('correct','wrong','blank','net')],p['demo']['score'],p['demo']['rank'],p['estimate']['rank'],r['status']]+[p['subjects'][x[0]]['net'] for x in subjects])
        return csv_response(rows,'ANA_PRG_DENEME.csv')

    @router.get('/settings')
    def settings(request:Request):
        require(request)
        return dict(values=s.settings(),credentials=dict(openai=bool(os.environ.get('OPENAI_API_KEY')),
            whatsapp=bool(os.environ.get('ANA_WHATSAPP_ACCESS_TOKEN') and os.environ.get('ANA_WHATSAPP_PHONE_NUMBER_ID'))))
    @router.patch('/settings')
    def settings_patch(request:Request,body:dict):
        require(request)
        allowed={'AI_MODEL','AI_MONTHLY_BUDGET_TL','WHATSAPP_MONTHLY_BUDGET_TL','USDTRY_RATE','WHATSAPP_ENABLED','SHADOW_MODE',
                 'AUTO_GENERATE_ENABLED','AUTO_AI_ENABLED','AI_JOB_LIMIT','WHATSAPP_MESSAGE_ESTIMATE_TL','AI_INPUT_USD_PER_MILLION','AI_OUTPUT_USD_PER_MILLION'}
        if set(body)-allowed:raise ValueError('Bu ayar değiştirilemez; secret/env kullanın.')
        for k,v in body.items():
            if k.endswith('_ENABLED') or k=='SHADOW_MODE':
                if str(v) not in ('true','false'):raise ValueError('Ayar true/false olmalı.')
            elif k=='AI_MODEL':
                if not isinstance(v,str) or len(v)>80 or not v.startswith('gpt-'):raise ValueError('Model adı geçersiz.')
            elif not 0<=float(v)<=100000:raise ValueError('Ayar aralık dışında.')
        with s.store.transaction('ADMIN','update-settings') as c:
            c.executemany('INSERT INTO ana_settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',[(k,str(v)) for k,v in body.items()])
        return dict(ok=True)
    @router.get('/system/health')
    def health(request:Request):require(request);return s.store.health()
    @router.get('/system/logs')
    def logs(request:Request,limit:int=100):
        require(request)
        with s.store.connect() as c:rows=[dict(r) for r in c.execute('SELECT * FROM ana_audit_log ORDER BY id DESC LIMIT ?',(max(1,min(500,limit)),))]
        return dict(items=rows)
    @router.post('/system/persist')
    def persist(request:Request):
        require(request)
        with s.store.lock:s.store.snapshot()
        return s.store.health()

    @router.get('/student/me')
    def student_me(request:Request):
        session=require(request,True);sid=session['student_id'];student=s.store.get('students',sid)
        assignments=s.store.rows('assignments',where='student_id=? AND active=1',args=(sid,),limit=100000)
        homework_ids={a['homework_id'] for a in assignments}
        homework=[s.public('homework_pool',h) for h in s.store.rows('homework_pool',limit=100000) if h['id'] in homework_ids]
        evaluations=s.store.rows('ai_evaluations',where="student_id=? AND active=1 AND status='APPROVED'",args=(sid,),limit=10000)
        results=s.store.rows('mock_results',where="student_id=? AND active=1 AND status='APPROVED'",args=(sid,),limit=10000)
        submissions=s.store.rows('submissions',where='student_id=? AND active=1',args=(sid,),limit=10000)
        videos=[v for v in s.store.rows('videos',limit=10000) if v.get('course') in student.get('courses',[])]
        return dict(student=s.public('students',student),assignments=assignments,homework=homework,evaluations=evaluations,
                    results=results,submissions=submissions,videos=videos)
    @router.get('/student/me/program')
    def student_program(request:Request,week:str=''):
        session=require(request,True);where='student_id=? AND active=1';args=[session['student_id']]
        if week:where+=' AND week=?';args.append(monday(week).isoformat())
        return dict(items=s.store.rows('assignments',where=where,args=tuple(args),limit=10000))
    @router.get('/student/me/results/{id}')
    def student_result(id:str,request:Request):
        session=require(request,True);row=s.store.get('mock_results',id)
        if row['student_id']!=session['student_id'] or row['status']!='APPROVED':raise HTTPException(403,'Bu sonuca erişim yetkiniz yok.')
        return row
    @router.get('/student/me/submissions/{id}')
    def student_submission(id:str,request:Request):
        session=require(request,True);row=s.store.get('submissions',id)
        if row['student_id']!=session['student_id']:raise HTTPException(403,'Bu teslime erişim yetkiniz yok.')
        return row

    app.include_router(router)
    assets=Path(__file__).parent/'web'
    @app.get('/ana-prg')
    @app.get('/ana-prg/{path:path}')
    def ana_page(path:str=''):
        if path in ('ana.css','ana.js'):return FileResponse(assets/path,media_type='text/css' if path.endswith('.css') else 'text/javascript')
        return FileResponse(assets/'index.html',media_type='text/html')
    return s
