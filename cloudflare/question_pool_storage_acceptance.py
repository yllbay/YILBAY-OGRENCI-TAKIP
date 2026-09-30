"""Storage policy acceptance using SQLite and a memory object store; no network."""
import hashlib
import importlib
import io
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
from contextlib import contextmanager
import question_pool_policy as policy
import runtime_storage as storage


class Missing(Exception):
    def __init__(self, code='NoSuchKey'):
        self.response = {'Error': {'Code': code}}


class Body(io.BytesIO):
    def iter_chunks(self, size):
        while data := self.read(size):
            yield data


class Store:
    def __init__(self):
        self.objects = {}
        self.deletes = []
    def etag(self, key):
        return '"' + hashlib.sha256(self.objects[key]).hexdigest() + '"'
    def get_paginator(self, name):
        return self
    def paginate(self, **kw):
        return [{'Contents': [{'Key': key, 'Size': len(data), 'ETag': self.etag(key)}
                              for key, data in self.objects.items() if key.startswith(kw['Prefix'])]}]
    def head_object(self, **kw):
        if kw['Key'] not in self.objects:
            raise Missing()
        return {'ETag': self.etag(kw['Key'])}
    def get_object(self, **kw):
        key = kw['Key']
        if key not in self.objects:
            raise Missing()
        return {'Body': Body(self.objects[key]), 'ETag': self.etag(key)}
    def copy_object(self, **kw):
        self.objects[kw['Key']] = self.objects[kw['CopySource']['Key']]
    def put_object(self, **kw):
        key = kw['Key']
        if kw.get('IfNoneMatch') == '*' and key in self.objects:
            raise Missing('PreconditionFailed')
        if kw.get('IfMatch') and (key not in self.objects or self.etag(key) != kw['IfMatch']):
            raise Missing('PreconditionFailed')
        body = kw['Body']
        self.objects[key] = body.read() if hasattr(body, 'read') else body
        return {'ETag': self.etag(key)}
    def upload_file(self, path, bucket, key, **kwargs):
        self.objects[key] = Path(path).read_bytes()
    def delete_object(self, **kwargs):
        self.deletes.append(kwargs['Key'])
        self.objects.pop(kwargs['Key'], None)


@contextmanager
def user(path):
    token = policy.WRITE_SCOPE.set({'actor':'disposable-user','user_intent':True,'path':path})
    try:
        yield
    finally:
        policy.WRITE_SCOPE.reset(token)


def install(con):
    token = policy.SCHEMA_SCOPE.set(True)
    try:
        policy.install_triggers(con)
        con.commit()
    finally:
        policy.SCHEMA_SCOPE.reset(token)


def blocked(con, sql):
    try:
        con.execute(sql)
    except sqlite3.DatabaseError:
        con.rollback()
    else:
        raise AssertionError('Automatic mutation allowed: '+sql)

store = Store()
sys.modules['boto3'] = types.SimpleNamespace(client=lambda *args, **kwargs: store)
sys.modules['botocore'] = types.ModuleType('botocore')
sys.modules['botocore.config'] = types.SimpleNamespace(Config=lambda **kwargs: None)
os.environ.update(R2_ACCOUNT_ID='disposable', R2_BUCKET_NAME='disposable',
                  AWS_ACCESS_KEY_ID='disposable', AWS_SECRET_ACCESS_KEY='disposable')

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    fixture = root / 'fixture.db'
    con = sqlite3.connect(fixture)
    con.executescript("""
      CREATE TABLE topics(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE questions(id INTEGER PRIMARY KEY,topic_id INTEGER,raw_crop_path TEXT,display_image_path TEXT);
      CREATE TABLE source_documents(id INTEGER PRIMARY KEY,stored_path TEXT);
      CREATE TABLE crop_sessions(id INTEGER PRIMARY KEY,status TEXT,x0 REAL,raw_crop_path TEXT,display_image_path TEXT);
      CREATE TABLE test_classes(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE exams(id INTEGER PRIMARY KEY,class_id INTEGER,name TEXT);
      CREATE TABLE exam_questions(exam_id INTEGER,question_id INTEGER,PRIMARY KEY(exam_id,question_id));
      CREATE TABLE auth_sessions(id INTEGER PRIMARY KEY,token TEXT);
      CREATE TABLE coaching_students(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE coaching_curriculum_topics(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE coach2_course_topics(id INTEGER PRIMARY KEY,name TEXT);
      INSERT INTO topics VALUES(1,'Existing Exact Name');
      INSERT INTO questions VALUES(1,1,'RawCrops/existing.png','DisplayImages/existing.png');
      INSERT INTO source_documents VALUES(1,'Sources/existing.pdf');
      INSERT INTO crop_sessions VALUES(1,'FINALIZED',0.123,'RawCrops/existing.png','DisplayImages/existing.png');
      INSERT INTO test_classes VALUES(1,'Existing Exam Folder');
      INSERT INTO exams VALUES(1,1,'Existing Exam');
      INSERT INTO exam_questions VALUES(1,1);
    """)
    con.close()
    store.objects['DATA/genesis.db'] = fixture.read_bytes()
    for key in ('RawCrops/existing.png', 'DisplayImages/existing.png', 'Sources/existing.pdf'):
        store.objects['DATA/' + key] = b'UNCHANGED-' + key.encode()
    storage.ROOT = root / 'first'
    storage.bootstrap()
    original = store.objects['DATA/genesis.db']
    policy.enable()
    con = sqlite3.connect(storage.ROOT / 'genesis.db')
    install(con)
    con.execute("INSERT INTO auth_sessions VALUES(1,'other-device-session')")
    con.execute("INSERT INTO coaching_students VALUES(1,'Preserved Coaching')")
    con.execute("INSERT INTO coaching_curriculum_topics VALUES(1,'Preserved Curriculum')")
    con.execute("INSERT INTO coach2_course_topics VALUES(1,'Preserved Course')")
    con.commit()
    for sql in ("UPDATE topics SET name='BAD' WHERE id=1", 'DELETE FROM questions WHERE id=1',
                'DELETE FROM exams WHERE id=1', 'DELETE FROM test_classes WHERE id=1',
                'DELETE FROM crop_sessions WHERE id=1', "INSERT INTO topics VALUES(2,'AUTO')",
                "INSERT INTO pool_user_changes(table_name,row_key,actor,action) VALUES('topics','[1]','fake','DELETE /api/topics/1')"):
        blocked(con, sql)
    con.close()
    storage.sync_once()
    assert store.objects['DATA/genesis.db'] == original
    assert storage.OPERATIONS_KEY in store.objects
    with user('POST /api/topics'):
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        con.execute("INSERT INTO topics VALUES(2,'New User Folder')")
        con.commit()
        blocked(con, "INSERT OR REPLACE INTO topics VALUES(1,'BAD')")
        blocked(con, "UPDATE pool_user_changes SET actor='tampered'")
        con.close()
        storage.sync_once(pool_write=True)
    revision = storage.pool_status()['revision']
    assert f'_snapshots/question-pool/{revision}.db' in store.objects
    with user('PATCH /api/topics/1'):
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        con.execute("UPDATE topics SET name='Explicit User Rename' WHERE id=1")
        con.commit()
        con.close()
        storage.sync_once(pool_write=True)
    # Rollback must not manufacture permission for a future background mutation.
    with user('DELETE /api/topics/2'):
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        seq = policy.journal_seq(con)
        con.execute('DELETE FROM topics WHERE id=2')
        con.rollback()
        assert policy.journal_seq(con) == seq
        con.close()
    (storage.ROOT / 'RawCrops/existing.png').unlink()
    storage.sync_once()
    assert not store.deletes
    assert (storage.ROOT / 'RawCrops/existing.png').is_file()
    # Simulate authorized exam deletion including composite-key relation rows.
    with user('DELETE /api/exams/1'):
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        con.execute('DELETE FROM exam_questions WHERE exam_id=1')
        con.execute('DELETE FROM exams WHERE id=1')
        con.commit()
        con.close()
        storage.sync_once(pool_write=True)
    with user('DELETE /api/questions/1'):
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        con.execute('DELETE FROM questions WHERE id=1')
        con.execute('DELETE FROM crop_sessions WHERE id=1')
        con.commit()
        con.close()
        # Fail asset removal AFTER the durable DB snapshot. Restart must finish
        # the original user's tombstone, not resurrect its question or images.
        real_delete = store.delete_object
        store.delete_object = lambda **kw: (_ for _ in ()).throw(OSError('disposable asset failure'))
        try:
            storage.sync_once(pool_write=True)
        except OSError:
            pass
        else:
            raise AssertionError('Asset failure was hidden')
        store.delete_object = real_delete
    storage.ROOT = root / 'second'
    storage._known = {}; storage._stats = {}; storage._locked_assets = {}
    storage.bootstrap()
    con = sqlite3.connect(storage.ROOT / 'genesis.db')
    assert con.execute('SELECT name FROM topics ORDER BY id').fetchall() == [('Explicit User Rename',), ('New User Folder',)]
    assert con.execute('SELECT count(*) FROM questions').fetchone()[0] == 0
    assert con.execute('SELECT count(*) FROM exams').fetchone()[0] == 0
    assert con.execute('SELECT count(*) FROM crop_sessions').fetchone()[0] == 0
    assert con.execute('SELECT token FROM auth_sessions').fetchone()[0] == 'other-device-session'
    assert con.execute('SELECT name FROM coaching_students').fetchone()[0] == 'Preserved Coaching'
    assert con.execute('SELECT name FROM coaching_curriculum_topics').fetchone()[0] == 'Preserved Curriculum'
    assert con.execute('SELECT name FROM coach2_course_topics').fetchone()[0] == 'Preserved Course'
    assert con.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    con.close()
    assert not (storage.ROOT / 'RawCrops/existing.png').exists()
    storage.sync_once()
    assert 'DATA/RawCrops/existing.png' not in store.objects
    assert 'DATA/DisplayImages/existing.png' not in store.objects
    assert 'DATA/Sources/existing.pdf' in store.objects
    # Missing files never authorize deletion of the remaining user's source.
    (storage.ROOT / 'Sources/existing.pdf').unlink()
    storage.sync_once()
    assert (storage.ROOT / 'Sources/existing.pdf').is_file()
    assert 'DATA/Sources/existing.pdf' not in store.deletes
    with user('DELETE /api/classes/1'):
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        con.execute('DELETE FROM test_classes WHERE id=1')
        con.commit()
        con.close()
        storage.sync_once(pool_write=True)
print('POOL_USER_EDITS_DELETES_AUDIT_AUTOMATION_BLOCKED_R2_RESTART_OK')
