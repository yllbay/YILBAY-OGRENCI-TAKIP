"""Full-app acceptance on a disposable Docker container only. Never run on production."""
import http.cookiejar
import io
import json
import os
from pathlib import Path
import sqlite3
import urllib.error
import urllib.request
import uuid
import fitz

BASE = 'http://127.0.0.1:8000'
clients = [urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
           for _ in range(2)]


def request(client, path, body=None, method=None, content_type='application/json', expected=200, intent=True):
    data = json.dumps(body).encode() if isinstance(body, dict) else body
    headers={'Content-Type': content_type}
    if intent and (method or ('POST' if data is not None else 'GET')) in {'POST','PUT','PATCH','DELETE'}:
        permit=request(client,'/api/question-pool/user-token')
        headers['X-Genesis-User-Intent']=intent if isinstance(intent,str) else permit['token']
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        response = client.open(req, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        assert response.status == expected, (path, response.status, raw[:300])
        if 'json' in response.headers.get('Content-Type', ''):
            return json.loads(raw)
        return raw


for client in clients:
    request(client, '/')
    assert request(client, '/api/auth/me')['authenticated']
first, second = clients
topic = request(first, '/api/topics', {'name': 'Gecici Kabul Alani', 'parent_id': None,
                                    'description': 'Disposable only', 'content': ''})
pdf = fitz.open()
page = pdf.new_page(width=600, height=600)
page.insert_text((100, 145), '1. What is 2 plus 2?', fontsize=20)
page.insert_text((115, 190), 'A) 4     B) 5     C) 6     D) 7     E) 8', fontsize=16)
content = pdf.tobytes()
pdf.close()
boundary = 'GENESIS-' + uuid.uuid4().hex
multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="disposable.pdf"\r\n'
             'Content-Type: application/pdf\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
source = request(first, '/api/sources/upload', multipart,
                 content_type=f'multipart/form-data; boundary={boundary}')
assert source['stored_path'].startswith('Sources/'), source
box = {'source_id': source['id'], 'topic_id': topic['id'], 'page_no': 1,
       'x0': .1, 'y0': .1, 'x1': .85, 'y1': .6, 'difficulty': 'ORTA',
       'batch_id': 'disposable-pool-acceptance'}
crop = request(first, '/api/crops/prepare', box)
saved = request(first, f"/api/crops/{crop['id']}/save-one", {'answer': 'A'})
qid = saved['question_id']
assert saved['number_mask']['diagnostics']['method'] == 'stored_crop_bbox', saved['number_mask']
db = sqlite3.connect('/app/DATA/genesis.db')
try:
    row = db.execute('select x0,y0,x1,y1,raw_crop_path,display_image_path,status from crop_sessions where id=?',
                     (crop['id'],)).fetchone()
    assert tuple(row[:4]) == tuple(box[k] for k in ('x0', 'y0', 'x1', 'y1')), row
    assert row[-1] == 'FINALIZED'
    assert Path('/app/DATA', row[4]).is_file(), 'Raw crop was deleted'
    assert Path('/app/DATA', row[5]).is_file()
    assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
finally:
    db.close()
assert request(second, '/api/topics')[0]['id'] == topic['id']
questions = request(second, f"/api/questions?topic_id={topic['id']}")
assert any(question['id'] == qid for question in questions), 'Second session did not see same pool'
request(second, f'/api/questions/{qid}/image')
before = request(first, '/api/internal/question-studio-fingerprint')
# Without the authenticated explicit-user permit, all old destructive routes stay blocked.
request(first, f'/api/questions/{qid}', method='DELETE', expected=403, intent=False)
request(first, f'/api/questions/{qid}', method='DELETE', expected=403,
        intent=request(second,'/api/question-pool/user-token')['token'])
request(first, f"/api/topics/{topic['id']}", {'name':'MUST NOT CHANGE'}, method='PATCH', expected=403, intent=False)
request(first, '/api/maintenance/stale-prepared', {}, expected=423)
assert request(first, '/api/internal/question-studio-fingerprint')['sha256'] == before['sha256']
# The same user can deliberately edit, move and delete, with normal dependency checks.
request(first, f"/api/topics/{topic['id']}", {'name':'Kullanici Duzenlemesi'}, method='PATCH')
request(first, f'/api/questions/{qid}/learning-outcome', {'learning_outcome':'User outcome'}, method='PUT')
assert request(second,f"/api/questions?topic_id={topic['id']}")[0]['learning_outcome']=='User outcome'
extra=request(first,'/api/topics',{'name':'Silinecek','parent_id':None})
request(first,f'/api/questions/{qid}/move',{'topic_id':extra['id']})
assert not request(second,f"/api/questions?topic_id={topic['id']}")
request(first,f'/api/questions/{qid}/move',{'topic_id':topic['id']})
request(first,f"/api/topics/{extra['id']}",method='DELETE')
assert len(request(second,'/api/topics'))==1
# Finalized coordinates and image files are removed ONLY because the user deleted the question.
request(first,f'/api/questions/{qid}',method='DELETE')
assert not request(second,f"/api/questions?topic_id={topic['id']}")
assert not Path('/app/DATA',row[4]).exists()
assert not Path('/app/DATA',row[5]).exists()
assert Path('/app/DATA',source['stored_path']).exists(), 'Shared source must survive question deletion'
# Recreate with real user crop/save APIs, then exercise the explicit double-confirm bulk delete.
crop=request(first,'/api/crops/prepare',box)
saved=request(first,f"/api/crops/{crop['id']}/save-one",{'answer':'A'})
request(first,'/api/questions/delete-all',{'topic_id':topic['id'],'confirm':'SIL'},expected=409)
assert len(request(second,f"/api/questions?topic_id={topic['id']}"))==1
request(first,'/api/questions/delete-all',{'topic_id':topic['id'],'confirm':'TÜMÜNÜ SİL'})
assert not request(second,f"/api/questions?topic_id={topic['id']}")
# Leave one disposable real question for the separate browser acceptance.
crop=request(first,'/api/crops/prepare',box)
saved=request(first,f"/api/crops/{crop['id']}/save-one",{'answer':'A'})
qid=saved['question_id']
test_folder=request(first,'/api/classes',{'name':'Gecici Sinif Dosyasi','parent_id':None})
exam=request(first,'/api/exams',{'name':'Silinecek Sinav','class_id':test_folder['id']})
request(first,f"/api/exams/{exam['id']}/questions",{'question_id':qid})
request(first,f"/api/exams/{exam['id']}",method='DELETE',expected=403,intent=False)
request(first,f"/api/classes/{test_folder['id']}",method='DELETE',expected=409)
request(first,f"/api/exams/{exam['id']}",method='DELETE')
request(first,f"/api/classes/{test_folder['id']}",method='DELETE')
assert not request(second,'/api/test-tree')
test_folder=request(first,'/api/classes',{'name':'Gecici Sinif Dosyasi','parent_id':None})
assert request(second,'/api/test-tree')[0]['id']==test_folder['id']
assert 'GENESIS_QUESTION_POOL_USER_OWNED_V2' in request(first,'/static/app-0.10.7.js').decode()
for route in ('/api/coaching/v3/classes', '/api/coaching/v3/curriculum', '/api/coaching/v2/students'):
    request(first, route, expected=410 if os.environ.get('ANA_PRG_RELEASE')=='1' else 200)
request(first, '/api/online/internet-test/genesis-audit-invalid-token', expected=404)
print('DISPOSABLE_USER_FOLDER_QUESTION_EXAM_EDITS_DELETES_TWO_SESSIONS_OK')
