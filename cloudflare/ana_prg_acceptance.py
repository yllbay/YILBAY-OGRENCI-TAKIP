"""Disposable native ANA integration tests; never use production data/providers."""
import sys,io,json,tempfile,unittest,hashlib,sqlite3,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from ana_prg.storage import Store,LocalObjects,SNAPSHOT_KEY
from ana_prg.service import Service
from ana_prg.api import install,BASE
from ana_prg.domain import FORMATS,calculate,validate_answers,build_plan,cohort
from ana_prg.providers import ProviderError

class FakeAI:
    def __init__(self):self.calls=[];self.result=None;self.error=None
    def read(self,**kwargs):
        self.calls.append({k:v for k,v in kwargs.items() if k!='data'})
        if self.error:raise self.error
        return self.result,{'status':'completed','usage':{'input_tokens':1000,'output_tokens':1500},'output':[]}
class FakeWhatsApp:
    def __init__(self):self.calls=[];self.error=None
    def send(self,**kwargs):
        self.calls.append(kwargs)
        if self.error:raise self.error
        return 'disposable-message-id'

def image_bytes():
    out=io.BytesIO();Image.new('RGB',(300,500),'white').save(out,'PNG');return out.getvalue()
def all_answers(kind,answer='A'):
    return [dict(subject=c,question_no=i+1,answer=answer) for c,l,q,w in FORMATS[kind]['subjects'] for i in range(q)]
def all_keys(kind):return {c:['A']*q for c,l,q,w in FORMATS[kind]['subjects']}

class Acceptance(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.objects=LocalObjects(self.root/'r2')
        self.store=Store(self.root/'runtime',self.objects);self.ai=FakeAI();self.wa=FakeWhatsApp();self.s=Service(self.store,self.ai,self.wa)
        self.app=FastAPI();install(self.app,self.root,self.s,lambda u,p:'verified-admin' if (u,p)==('admin','test-password') else None,
            lambda t:{'role':'ADMIN'} if t in ('verified-admin','automatic-admin') else None)
        self.teacher=TestClient(self.app);r=self.teacher.post(BASE+'/auth/teacher-login',json={'username':'admin','password':'test-password'})
        self.assertEqual(r.status_code,200);self.teacher.headers['X-ANA-CSRF']=r.json()['csrf']
        self.cls=self.create('classes',dict(name='Test sınıfı'))
        self.a=self.create('students',dict(name='<script>alert(1)</script>',code='A_TEST',pin='1234',class_id=self.cls['id'],courses=['TYT_MAT'],phone='+905000000000',opt_in=True))
        self.b=self.create('students',dict(name='Öğrenci B',code='B_TEST',pin='5678',class_id=self.cls['id'],courses=['TYT_GEO']))
    def tearDown(self):self.teacher.close();self.temp.cleanup()
    def req(self,path,method='GET',payload=None,status=200,client=None):
        r=(client or self.teacher).request(method,BASE+path,json=payload)
        self.assertEqual(r.status_code,status,(path,r.text[:500]));return r.json()
    def create(self,path,payload):return self.req('/'+path,'POST',payload)
    def student(self,code='A_TEST',pin='1234'):
        c=TestClient(self.app);r=c.post(BASE+'/student/auth/login',json={'code':code,'pin':pin});self.assertEqual(r.status_code,200,r.text)
        c.headers['X-ANA-CSRF']=r.json()['csrf'];return c
    def live(self):self.req('/settings','PATCH',{'SHADOW_MODE':'false','WHATSAPP_ENABLED':'true'})
    def optical(self,kind='TYT',student=None,confidence=.99):
        ex=self.create('mock-exams',dict(name='Test deneme '+kind,kind=kind,date='2026-10-01'))
        self.req('/mock-exams/'+ex['id']+'/answer-key','POST',dict(key=all_keys(kind)))
        file=self.s.upload('optik.png','image/png',image_bytes(),'TEST',(student or self.a)['id'],'optics')
        job=self.req('/mock-exams/'+ex['id']+'/optics/whole','POST',dict(student_id=(student or self.a)['id'],file_id=file['id']))
        self.ai.result=dict(answers=all_answers(kind),confidence=confidence,feedback='Okundu')
        return ex,file,job

    def test_schema_and_transactional_R2_restore(self):
        before=self.store.health()['counts'];self.store.initialize()
        self.assertEqual(before,self.store.health()['counts'])
        restored=Store(self.root/'restart',self.objects)
        self.assertTrue(restored.restored);self.assertEqual(restored.health()['counts'],before)
        self.assertEqual(restored.get('students',self.a['id'])['code'],'A_TEST')
        with self.store.connect() as c:self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
        original=self.objects.put
        def fail(key,*args,**kwargs):
            if key==SNAPSHOT_KEY:raise RuntimeError('DISPOSABLE_FAILURE')
            return original(key,*args,**kwargs)
        self.objects.put=fail
        with self.assertRaises(RuntimeError):self.s.save('classes',dict(name='Must roll back'),'TEST')
        self.objects.put=original
        self.assertEqual(self.store.health()['counts']['classes'],before['classes'])

    def test_teacher_student_authorization_csrf_ownership(self):
        anon=TestClient(self.app);anon.cookies.set('genesis_session','automatic-admin')
        self.req('/students',status=401,client=anon)
        anon.post(BASE+'/auth/teacher-login',json={'username':'admin','password':'wrong'})
        student=self.student();self.req('/students',status=403,client=student)
        self.req('/classes','POST',dict(name='Denied'),status=403,client=student)
        me=self.req('/student/me',client=student);self.assertEqual(me['student']['id'],self.a['id'])
        self.assertNotIn('pin_hash',me['student']);self.assertNotIn('pin',me['student'])
        other=self.s.upload('b.png','image/png',image_bytes(),'TEST',self.b['id'],'submissions')
        r=student.get(BASE+'/files/'+other['id']+'/content');self.assertEqual(r.status_code,403)
        no_csrf=TestClient(self.app);no_csrf.cookies.update(self.teacher.cookies)
        self.req('/classes','POST',{'name':'Denied'},403,no_csrf)
        r=self.teacher.post(BASE+'/classes',json={'name':'Denied'},headers={'Origin':'https://evil.example'});self.assertEqual(r.status_code,403)
        with self.store.transaction('TEST','expire') as c:c.execute('UPDATE ana_sessions SET expires_at=0 WHERE role=\'STUDENT\'')
        self.req('/student/me',status=401,client=student)

    def test_pin_five_attempt_lockout(self):
        student=TestClient(self.app)
        for _ in range(5):self.req('/student/auth/login','POST',{'code':'A_TEST','pin':'wrong'},400,student)
        self.req('/student/auth/login','POST',{'code':'A_TEST','pin':'1234'},400,student)
        row=self.store.get('students',self.a['id']);self.assertGreater(row['locked_until'],time.time())
        with self.store.transaction('TEST','unlock') as c:self.store.put('students',{**row,'locked_until':0},c)
        self.student()

    def test_weekly_selected_courses_idempotency_and_order(self):
        for order in (3,1,2):self.create('homework',dict(name=f'PDF {order}',source='Kitap',course='TYT_MAT',order=order,test_no=order,questions=5))
        self.create('course-rules',dict(course='TYT_MAT',days=[0,1],order=1))
        self.create('course-rules',dict(course='TYT_GEO',days=[0],order=2))
        p=dict(week='2030-01-07',skip_past=False)
        preview=self.req('/programs/generate','POST',{**p,'preview':True});self.assertEqual(preview['created'],2)
        first=self.req('/programs/generate','POST',p);self.assertEqual(first['assignments'],2)
        repeat=self.req('/programs/generate','POST',p);self.assertEqual(repeat['created'],0)
        assignments=self.req('/assignments')['items'];self.assertEqual(len(assignments),2)
        self.assertTrue(all(a['student_id']==self.a['id'] for a in assignments))
        slots=sorted(self.req('/program-slots')['items'],key=lambda r:r['day'])
        self.assertEqual([self.store.get('homework_pool',s['homework_id'])['order'] for s in slots],[1,2])
        next_week=self.req('/programs/generate','POST',dict(week='2030-01-14',skip_past=False))
        self.assertEqual(next_week['created'],1)
        self.req('/programs/reset','POST',dict(week='2030-01-07'))
        reset=self.req('/programs/generate','POST',p);self.assertEqual(reset['created'],2)

    def test_file_submission_homework_AI_and_review(self):
        import fitz
        doc=fitz.open();doc.new_page().insert_text((70,80),'Homework');pdf=doc.tobytes();doc.close()
        file=self.s.upload('test.pdf','application/pdf',pdf,'TEST',None,'homework')
        h=self.create('homework',dict(name='Ödev',source='Kaynak',course='TYT_MAT',order=1,test_no=1,questions=3,file_id=file['id']))
        assignment=self.create('assignments',dict(student_id=self.a['id'],homework_id=h['id'],date='2030-01-07'))
        student=self.student();r=student.get(BASE+'/files/'+file['id']+'/content');self.assertEqual(r.status_code,200)
        self.assertEqual(hashlib.sha256(r.content).hexdigest(),file['sha256'])
        submission_file=self.s.upload('cevap.png','image/png',image_bytes(),'TEST',self.a['id'],'submissions')
        sub=self.req('/submissions','POST',dict(assignment_id=assignment['id'],file_id=submission_file['id']),client=student)
        other=self.student('B_TEST','5678');self.req('/student/me/submissions/'+sub['id'],status=403,client=other)
        self.req('/submissions','POST',dict(assignment_id=assignment['id'],file_id=submission_file['id']),400,other)
        self.req('/homework/'+h['id']+'/answer-key','POST',dict(answers=['A','B','C']))
        job=self.req('/ai/queue','POST',dict(kind='submission',submission_id=sub['id']))
        repeat=self.req('/ai/queue','POST',dict(kind='submission',submission_id=sub['id']));self.assertEqual(job['id'],repeat['id'])
        self.ai.result=dict(answers=[dict(subject='HOMEWORK',question_no=i+1,answer=a) for i,a in enumerate(['A','E',''])],confidence=.8,feedback='Kontrol gerekli')
        self.live();self.s.process_jobs()
        evaluation=self.req('/evaluations')['items'][0];self.assertEqual((evaluation['correct'],evaluation['wrong'],evaluation['blank'],evaluation['net']),(1,1,1,.75))
        self.assertEqual(self.req('/student/me',client=student)['evaluations'],[])
        self.req('/evaluations/'+evaluation['id']+'/review','POST',dict(answers=['A','B','C']))
        self.assertEqual(self.req('/student/me',client=student)['evaluations'][0]['net'],3)
        r=self.teacher.post(BASE+'/files/upload',files={'file':('bad.png',b'%PDF-bad','image/png')},data={'category':'optics'});self.assertEqual(r.status_code,400)
        r=self.teacher.post(BASE+'/files/upload',files={'file':('bad.txt',b'text','text/plain')});self.assertEqual(r.status_code,400)

    def test_whole_optical_TYT_AYT_single_call_and_history(self):
        self.live()
        for kind in FORMATS:
            ex,file,job=self.optical(kind);before=len(self.ai.calls);self.s.process_jobs()
            self.assertEqual(len(self.ai.calls)-before,1)
            self.assertEqual(self.store.get('ai_queue',job['id'])['provider_calls'],1)
            result=self.req('/mock-exams/'+ex['id']+'/results')['results'][0]
            self.assertEqual(result['status'],'REVIEW')
            result=self.req('/mock-optics/'+result['optical_id']+'/approve','POST',dict(answers=all_answers(kind)))
            self.assertEqual(result['report']['totals']['net'],120 if kind=='TYT' else 80)
            self.assertEqual(result['report']['totals']['wrong'],0)
            self.assertEqual(result['status'],'APPROVED')
            if kind!='TYT':self.assertIsNotNone(result['report']['estimate']['paired_tyt_exam_id'])
        student=self.student();self.assertEqual(len(self.req('/student/me',client=student)['results']),3)
        other=self.student('B_TEST','5678');self.req('/student/me/results/'+result['id'],status=403,client=other)

    def test_low_confidence_reject_duplicate_incomplete_recovery(self):
        self.live();ex,file,job=self.optical(confidence=.7);self.s.process_jobs()
        student=self.student();self.assertEqual(self.req('/student/me',client=student)['results'],[])
        o=self.req('/mock-optics')['items'][0]
        result=self.req('/mock-optics/'+o['id']+'/approve','POST',dict(answers=all_answers('TYT')))
        self.assertEqual(result['status'],'APPROVED');self.assertEqual(len(self.req('/student/me',client=student)['results']),1)
        ex2,file2,job2=self.optical();self.ai.result['answers'][-1]=dict(self.ai.result['answers'][0]);self.s.process_jobs()
        self.assertEqual(self.store.get('ai_queue',job2['id'])['status'],'FAILED')
        self.assertIsNotNone(self.store.get('ai_queue',job2['id'])['raw'])
        self.assertIsNotNone(self.store.get('ai_queue',job2['id'])['normalized'])
        self.assertEqual(self.req('/mock-exams/'+ex2['id']+'/results')['results'],[])
        self.req('/ai/queue/'+job2['id']+'/retry','POST',{})
        with self.store.transaction('TEST','interrupt') as c:self.store.put('ai_queue',{**self.store.get('ai_queue',job2['id'],c),'status':'RUNNING'},c)
        restored=Service(Store(self.root/'coldstart',self.objects),self.ai,self.wa)
        self.assertEqual(restored.store.get('ai_queue',job2['id'])['status'],'UNCERTAIN')

    def test_whatsapp_optin_duplicate_and_ambiguous_no_resend(self):
        self.live();template=self.create('templates',dict(name='Test',provider_name='test_template',language='tr'))
        self.req('/whatsapp/queue','POST',dict(student_id=self.b['id'],template_id=template['id'],context='Test'),400)
        payload=dict(student_id=self.a['id'],template_id=template['id'],context='Test',parameters=['Haftalık rapor'])
        row=self.req('/whatsapp/queue','POST',payload);repeat=self.req('/whatsapp/queue','POST',payload);self.assertEqual(row['id'],repeat['id'])
        self.req('/whatsapp/queue/'+row['id']+'/send','POST',{});self.req('/whatsapp/queue/'+row['id']+'/send','POST',{})
        self.assertEqual(len(self.wa.calls),1)
        second=self.req('/whatsapp/queue','POST',{**payload,'context':'Test2'});self.wa.error=ProviderError('TEST_UNCERTAIN',True)
        self.req('/whatsapp/queue/'+second['id']+'/send','POST',{},400)
        self.req('/whatsapp/queue/'+second['id']+'/retry','POST',{},400)
        self.assertEqual(self.store.get('whatsapp_queue',second['id'])['status'],'UNCERTAIN')

    def test_batch_item_analysis_csv_injection_and_shadow(self):
        ex,file,job=self.optical()
        with self.assertRaises(ValueError):self.s.process_jobs()
        self.assertEqual(len(self.ai.calls),0)
        self.live();self.s.process_jobs()
        batch=self.req('/mock-exams/'+ex['id']+'/optics/batch','POST',dict(items=[dict(student_id=self.a['id'],file_id=file['id'])]))
        self.assertEqual(batch['items'][0]['job']['id'],job['id'])
        self.s.save('students',dict(name='=HYPERLINK("evil")'),'TEST',self.a['id'])
        # Recalculate with the updated name; server keeps formulas inert in CSV.
        self.s.save_key(ex['id'],all_keys('TYT'),'TEST')
        r=self.teacher.get(BASE+'/mock-exams/'+ex['id']+'/export.csv');self.assertEqual(r.status_code,200)
        self.assertIn("'=HYPERLINK",r.text)
        data=self.req('/mock-exams/'+ex['id']+'/results');self.assertEqual(len(data['item_analysis']),120)
        self.assertTrue(all(i['discrimination'] is None for i in data['item_analysis']))

    def test_route_pages_and_archive_dependencies(self):
        for path in ('','program','classes','homework','assignments','submissions','ai','whatsapp','mock-exams','reports','settings','system','student'):
            r=self.teacher.get('/ana-prg'+('/'+path if path else ''));self.assertEqual(r.status_code,200)
            self.assertNotIn('<iframe',r.text);self.assertIn('/ana-prg/ana.js',r.text)
        self.req('/classes/'+self.cls['id'],'DELETE',{},400)
        student=self.student();self.req('/students/'+self.a['id'],'DELETE',{})
        self.req('/student/me',status=401,client=student)
        self.assertEqual(self.teacher.get('/coaching').status_code,410)
        self.assertEqual(self.teacher.get('/api/coaching/v3/classes').status_code,410)

if __name__=='__main__':unittest.main(verbosity=2)
