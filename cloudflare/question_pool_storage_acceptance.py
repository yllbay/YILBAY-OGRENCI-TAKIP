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
    con.executescript('''
      CREATE TABLE topics(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE questions(id INTEGER PRIMARY KEY,topic_id INTEGER,raw_crop_path TEXT,display_image_path TEXT);
      CREATE TABLE source_documents(id INTEGER PRIMARY KEY,stored_path TEXT);
      CREATE TABLE crop_sessions(id INTEGER PRIMARY KEY,status TEXT,x0 REAL);
      CREATE TABLE auth_sessions(id INTEGER PRIMARY KEY,token TEXT);
      CREATE TABLE coaching_students(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE coaching_curriculum_topics(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE coach2_course_topics(id INTEGER PRIMARY KEY,name TEXT);
      INSERT INTO topics VALUES(1,'Existing Exact Name');
      INSERT INTO questions VALUES(1,1,'RawCrops/existing.png','DisplayImages/existing.png');
      INSERT INTO source_documents VALUES(1,'Sources/existing.pdf');
      INSERT INTO crop_sessions VALUES(1,'FINALIZED',0.123);
    ''')
    con.close()
    store.objects['DATA/genesis.db'] = fixture.read_bytes()
    for key in ('RawCrops/existing.png', 'DisplayImages/existing.png', 'Sources/existing.pdf'):
        store.objects['DATA/' + key] = b'UNCHANGED-' + key.encode()
    storage.ROOT = root / 'first'
    storage.bootstrap()
    original = store.objects['DATA/genesis.db']
    policy.enable()
    con = sqlite3.connect(storage.ROOT / 'genesis.db')
    policy.install_triggers(con)
    con.commit()
    con.execute("INSERT INTO auth_sessions VALUES(1,'other-device-session')")
    con.execute("INSERT INTO coaching_students VALUES(1,'Preserved Coaching')")
    con.execute("INSERT INTO coaching_curriculum_topics VALUES(1,'Preserved Curriculum')")
    con.execute("INSERT INTO coach2_course_topics VALUES(1,'Preserved Course')")
    con.commit()
    con.close()
    storage.sync_once()
    assert store.objects['DATA/genesis.db'] == original, 'Auth/coaching overwrote authoritative pool'
    assert storage.OPERATIONS_KEY in store.objects
    token = policy.WRITE_SCOPE.set({'new_rows': {}, 'path': '/api/topics'})
    try:
        con = sqlite3.connect(storage.ROOT / 'genesis.db')
        con.execute("INSERT INTO topics VALUES(2,'New User Folder')")
        con.commit()
        for sql in ("UPDATE topics SET name='BAD' WHERE id=1", 'DELETE FROM questions WHERE id=1',
                    "INSERT OR REPLACE INTO topics VALUES(1,'BAD')"):
            try:
                con.execute(sql)
            except sqlite3.DatabaseError:
                con.rollback()
            else:
                raise AssertionError('Immutable row mutation allowed: ' + sql)
        con.close()
        # Background sync racing the successful request must not swallow its durable commit.
        storage.sync_once()
        assert store.objects['DATA/genesis.db'] == original
        storage.sync_once(pool_write=True)
    finally:
        policy.WRITE_SCOPE.reset(token)
    assert store.objects['DATA/genesis.db'] != original
    revision = storage.pool_status()['revision']
    assert f'_snapshots/question-pool/{revision}.db' in store.objects
    # Local deletion does not authorize an R2 deletion.
    (storage.ROOT / 'RawCrops/existing.png').unlink()
    storage.sync_once()
    assert not store.deletes, store.deletes
    assert 'DATA/RawCrops/existing.png' in store.objects
    # Simulate replacement with a fresh ephemeral filesystem, reading only central R2.
    storage.ROOT = root / 'second'
    storage._known = {}; storage._stats = {}; storage._locked_assets = {}
    storage.bootstrap()
    con = sqlite3.connect(storage.ROOT / 'genesis.db')
    assert con.execute('SELECT name FROM topics ORDER BY id').fetchall() == [('Existing Exact Name',), ('New User Folder',)]
    assert con.execute('SELECT token FROM auth_sessions').fetchone()[0] == 'other-device-session'
    assert con.execute('SELECT name FROM coaching_students').fetchone()[0] == 'Preserved Coaching'
    assert con.execute('SELECT name FROM coaching_curriculum_topics').fetchone()[0] == 'Preserved Curriculum'
    assert con.execute('SELECT name FROM coach2_course_topics').fetchone()[0] == 'Preserved Course'
    assert con.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    con.close()
    assert (storage.ROOT / 'RawCrops/existing.png').read_bytes() == store.objects['DATA/RawCrops/existing.png']
print('POOL_APPEND_ONLY_SCOPED_SNAPSHOT_OPERATIONS_ISOLATION_RESTART_OK')
