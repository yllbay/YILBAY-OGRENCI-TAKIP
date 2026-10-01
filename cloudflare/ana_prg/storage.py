"""ANA-only local SQLite, CAS snapshots, immutable verified object storage."""
from __future__ import annotations
import contextlib, hashlib, json, os, sqlite3, threading, time, uuid
from pathlib import Path

TABLES = ('classes students homework_pool assignments submissions answer_keys '
          'ai_evaluations ai_queue guardians whatsapp_queue whatsapp_templates '
          'course_rules programs program_slots progress videos topic_order ai_references '
          'costs weekly_reports mock_exams mock_optics mock_results files').split()
RELATIONS = {'class_id':'classes', 'student_id':'students', 'homework_id':'homework_pool',
             'assignment_id':'assignments', 'submission_id':'submissions',
             'exam_id':'mock_exams', 'file_id':'files'}
SNAPSHOT_KEY = 'ANA_PRG/runtime/ana.db'

class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

def now():
    import datetime
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec='seconds')

def ident(prefix='ANA'):
    return prefix + '-' + uuid.uuid4().hex[:16].upper()

def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

def unpack(row):
    if row is None: return None
    result = json.loads(row['data'])
    result.update(id=row['id'], active=bool(row['active']), created_at=row['created_at'], updated_at=row['updated_at'])
    return result

class LocalObjects:
    """Explicit disposable-test/local adapter; production never falls back here."""
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def path(self, key):
        if not key.startswith('ANA_PRG/') or '..' in key.split('/') or '\\' in key: raise ValueError('Unsafe ANA object key')
        p=self.root/key
        assert p.resolve().is_relative_to(self.root.resolve())
        return p
    def get(self,key):
        p=self.path(key)
        if not p.exists(): return None,None
        value=p.read_bytes(); return value,hashlib.sha256(value).hexdigest()
    def put(self,key,value,etag=None,create=False,mime='application/octet-stream'):
        old,old_etag=self.get(key)
        if (create and old is not None) or (etag is not None and etag!=old_etag): raise RuntimeError('ANA_SNAPSHOT_CONFLICT')
        p=self.path(key);p.parent.mkdir(parents=True,exist_ok=True)
        tmp=p.with_suffix('.tmp');tmp.write_bytes(value);os.replace(tmp,p)
        return hashlib.sha256(value).hexdigest()

class R2Objects:
    def __init__(self):
        import boto3
        from botocore.config import Config
        self.bucket=os.environ['R2_BUCKET_NAME']
        self.client=boto3.client('s3',endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name='auto',config=Config(connect_timeout=10,read_timeout=45,retries={'max_attempts':2}))
    def get(self,key):
        if not key.startswith('ANA_PRG/'): raise ValueError('ANA object namespace required')
        try:
            r=self.client.get_object(Bucket=self.bucket,Key=key)
            return r['Body'].read(),r['ETag']
        except self.client.exceptions.ClientError as e:
            if e.response.get('Error',{}).get('Code') in ('NoSuchKey','404'): return None,None
            raise
    def put(self,key,value,etag=None,create=False,mime='application/octet-stream'):
        if not key.startswith('ANA_PRG/'): raise ValueError('ANA object namespace required')
        args=dict(Bucket=self.bucket,Key=key,Body=value,ContentType=mime,Metadata={'sha256':hashlib.sha256(value).hexdigest()})
        if create: args['IfNoneMatch']='*'
        elif etag is not None: args['IfMatch']=etag
        r=self.client.put_object(**args)
        return r['ETag']

class Store:
    def __init__(self, root=None, objects=None):
        self.root=Path(root or os.environ.get('ANA_RUNTIME_ROOT','/app/ANA_RUNTIME'))
        self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'ana.db'
        self.objects=objects or R2Objects()
        self.lock=threading.RLock();self.etag=None;self.last_sync=None;self.last_error=None;self.restored=False
        value,self.etag=self.objects.get(SNAPSHOT_KEY)
        if value is not None:
            tmp=self.root/'restore.tmp';tmp.write_bytes(value)
            with sqlite3.connect(tmp,factory=ClosingConnection) as c:
                if c.execute('PRAGMA quick_check').fetchone()[0]!='ok': raise RuntimeError('ANA_SNAPSHOT_CORRUPT')
                tables=[x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                if any(not t.startswith('ana_') and t!='sqlite_sequence' for t in tables): raise RuntimeError('ANA_NONOWNED_TABLE')
            os.replace(tmp,self.path);self.restored=True
        self.initialize()

    def connect(self):
        con=sqlite3.connect(self.path,timeout=30,isolation_level=None,factory=ClosingConnection)
        con.row_factory=sqlite3.Row;con.execute('PRAGMA foreign_keys=ON');con.execute('PRAGMA busy_timeout=30000')
        return con

    def initialize(self):
        with self.transaction('system','schema-v1') as c:
            c.execute('CREATE TABLE IF NOT EXISTS ana_schema(version INTEGER PRIMARY KEY,applied_at TEXT NOT NULL)')
            for t in TABLES:
                c.execute(f'''CREATE TABLE IF NOT EXISTS ana_{t}(
                    id TEXT PRIMARY KEY,data TEXT NOT NULL CHECK(json_valid(data)),active INTEGER NOT NULL DEFAULT 1,
                    student_id TEXT,class_id TEXT,homework_id TEXT,assignment_id TEXT,submission_id TEXT,exam_id TEXT,file_id TEXT,
                    course TEXT,week TEXT,status TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES ana_students(id),FOREIGN KEY(class_id) REFERENCES ana_classes(id),
                    FOREIGN KEY(homework_id) REFERENCES ana_homework_pool(id),FOREIGN KEY(assignment_id) REFERENCES ana_assignments(id),
                    FOREIGN KEY(submission_id) REFERENCES ana_submissions(id),FOREIGN KEY(exam_id) REFERENCES ana_mock_exams(id),
                    FOREIGN KEY(file_id) REFERENCES ana_files(id))''')
                for column in ('student_id','course','status','week','exam_id'):
                    c.execute(f'CREATE INDEX IF NOT EXISTS ana_{t}_{column}_idx ON ana_{t}({column},active)')
            c.executescript('''
                CREATE UNIQUE INDEX IF NOT EXISTS ana_students_code ON ana_students(json_extract(data,'$.code'));
                CREATE UNIQUE INDEX IF NOT EXISTS ana_results_pair ON ana_mock_results(exam_id,student_id);
                CREATE UNIQUE INDEX IF NOT EXISTS ana_slot_pair ON ana_program_slots(week,course,json_extract(data,'$.day'));
                CREATE TABLE IF NOT EXISTS ana_sessions(token_hash TEXT PRIMARY KEY,role TEXT NOT NULL,student_id TEXT,
                    csrf TEXT NOT NULL,expires_at INTEGER NOT NULL,FOREIGN KEY(student_id) REFERENCES ana_students(id));
                CREATE TABLE IF NOT EXISTS ana_audit_log(id INTEGER PRIMARY KEY,actor TEXT NOT NULL,event TEXT NOT NULL,
                    entity_id TEXT,detail TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ana_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS ana_rate_limits(key TEXT PRIMARY KEY,attempts INTEGER NOT NULL,window_start INTEGER NOT NULL);
            ''')
            c.execute('INSERT OR IGNORE INTO ana_schema VALUES(1,?)',(now(),))
            defaults={'AI_MODEL':'gpt-5.6-luna','AI_MONTHLY_BUDGET_TL':'300','WHATSAPP_MONTHLY_BUDGET_TL':'100',
                      'USDTRY_RATE':'50','WHATSAPP_ENABLED':'false','SHADOW_MODE':'true','AI_JOB_LIMIT':'3',
                      'AI_INPUT_USD_PER_MILLION':'0.20','AI_OUTPUT_USD_PER_MILLION':'1.20'}
            c.executemany('INSERT OR IGNORE INTO ana_settings VALUES(?,?)',defaults.items())

    def snapshot(self, connection=None):
        temp=self.root/'snapshot.tmp'
        if connection is not None:
            value=connection.serialize()
        else:
            with self.connect() as source, sqlite3.connect(temp,factory=ClosingConnection) as target: source.backup(target)
            value=temp.read_bytes()
        try:self.etag=self.objects.put(SNAPSHOT_KEY,value,etag=self.etag,create=self.etag is None,mime='application/x-sqlite3')
        except Exception as e:
            self.last_error=type(e).__name__
            raise
        self.last_sync=now();self.last_error=None;temp.unlink(missing_ok=True)

    @contextlib.contextmanager
    def transaction(self,actor,event,entity_id=None):
        with self.lock:
            c=self.connect()
            try:
                c.execute('BEGIN IMMEDIATE')
                yield c
                c.execute('INSERT INTO ana_audit_log(actor,event,entity_id,detail,created_at) VALUES(?,?,?,?,?)',
                          (actor,event,entity_id,'{}',now()))
                # Persist the consistent serialized transaction before acknowledging
                # or committing locally. Failed R2 writes roll back ANA rows.
                self.snapshot(c)
                c.commit()
            except Exception as e:
                c.rollback()
                raise
            finally: c.close()

    def get(self,t,id,c=None,required=True):
        assert t in TABLES
        if c is None:
            with self.connect() as con: row=con.execute(f'SELECT * FROM ana_{t} WHERE id=?',(id,)).fetchone()
        else: row=c.execute(f'SELECT * FROM ana_{t} WHERE id=?',(id,)).fetchone()
        if row is None and required: raise ValueError('Kayıt bulunamadı.')
        return unpack(row)

    def rows(self,t,c=None,where='active=1',args=(),limit=500,offset=0):
        assert t in TABLES
        sql=f'SELECT * FROM ana_{t} WHERE {where} ORDER BY created_at DESC,id LIMIT ? OFFSET ?'
        if c is None:
            with self.connect() as con: result=con.execute(sql,(*args,limit,offset)).fetchall()
        else: result=c.execute(sql,(*args,limit,offset)).fetchall()
        return [unpack(r) for r in result]

    def put(self,t,item,c):
        assert t in TABLES
        id=item.get('id') or ident(t[:3].upper());old=self.get(t,id,c,False)
        value={**(old or {}),**item,'id':id};stamp=now()
        columns=['student_id','class_id','homework_id','assignment_id','submission_id','exam_id','file_id','course','week','status']
        c.execute(f'''INSERT INTO ana_{t}(id,data,active,{','.join(columns)},created_at,updated_at)
            VALUES({','.join('?' for _ in range(15))}) ON CONFLICT(id) DO UPDATE SET
            data=excluded.data,active=excluded.active,{','.join(f'{k}=excluded.{k}' for k in columns)},updated_at=excluded.updated_at''',
            (id,encode(value),int(value.get('active',True)),*[value.get(k) or None for k in columns],(old or {}).get('created_at',stamp),stamp))
        return self.get(t,id,c)

    def settings(self,c=None):
        if c is None:
            with self.connect() as con: return dict(con.execute('SELECT key,value FROM ana_settings'))
        return dict(c.execute('SELECT key,value FROM ana_settings'))

    def health(self):
        with self.connect() as c:
            integrity=c.execute('PRAGMA quick_check').fetchone()[0]
            counts={t:c.execute(f'SELECT count(*) FROM ana_{t} WHERE active=1').fetchone()[0] for t in TABLES}
        return dict(ok=integrity=='ok' and self.last_error is None,version=1,counts=counts,
                    restored=self.restored,last_sync=self.last_sync,last_error=self.last_error,snapshot_key=SNAPSHOT_KEY)
