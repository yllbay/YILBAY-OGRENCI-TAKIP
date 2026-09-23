"""Write tests only against explicitly isolated canary; never production."""
import http.cookiejar, json, os, time, urllib.request, urllib.error
base=os.environ['CANARY_URL']
assert 'genesis-v3-check-' in base and 'genesis-web-0152' not in base
jar=http.cookiejar.CookieJar()
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
checks=0
def req(path, method='GET', data=None, expected=200, raw=None, ctype='application/json'):
    global checks
    body=json.dumps(data).encode() if data is not None else raw
    r=urllib.request.Request(base+path,data=body,method=method,headers={'Content-Type':ctype,'X-Genesis-Canary':os.environ['CANARY_TOKEN'],'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36','Accept':'application/json,text/html;q=0.9,*/*;q=0.8'})
    try:
        with op.open(r,timeout=30) as response: code=response.status; out=response.read()
    except urllib.error.HTTPError as e: code=e.code;out=e.read()
    assert code==expected, (path,method,code,out[:500])
    checks+=1
    try:return json.loads(out)
    except ValueError:return out
for attempt in range(30):
    try:
        req('/'); break
    except Exception:
        if attempt==29:raise
        time.sleep(5)
assert req('/api/auth/me')['role']=='ADMIN'
req('/api/coaching/curriculum/action','POST',{'action':'add-path','course':'Canary Matematik','unit':'Fonksiyon','topic':'Kavram','sort_order':1})
tree=req('/api/coaching/v3/curriculum')['courses']; c=next(x for x in tree if x['name']=='Canary Matematik');cid=c['id'];uid=c['units'][0]['id'];tid=c['units'][0]['topics'][0]['id']
cls=req('/api/coaching/v3/classes','POST',{'name':'Canary 12-A','difficulty_level':'MEDIUM'});cl=cls['id']
req('/api/coaching/v3/classes','POST',{'name':'Canary 12-A','difficulty_level':'MEDIUM'},409)
s=req('/api/coaching/v3/students','POST',{'name':'Canary Öğrenci','number':'CANARY-V3','class_id':cl});sid=s['student']['id'];assert s['effective_level']=='MEDIUM'
req('/api/coaching/v3/students','POST',{'name':'Canary Öğrenci','number':'CANARY-V3'},409)
req(f'/api/coaching/v3/CLASS/{cl}/courses','PUT',{'curriculum_course_id':cid,'weekly_sessions':2,'minutes':45})
req(f'/api/coaching/v3/CLASS/{cl}/responsibilities','PUT',{'curriculum_course_id':cid,'selections':[{'unit_id':uid,'topic_id':tid}]})
req(f'/api/coaching/v3/CLASS/{cl}/responsibilities','PUT',{'curriculum_course_id':cid,'selections':[{'unit_id':999999,'topic_id':tid}]},400)
for i in range(2): req('/api/coaching/v3/resources/link','POST',{'curriculum_course_id':cid,'unit_id':uid,'topic_id':tid,'title':f'Canary Video {i}','kind':'VIDEO','difficulty':'MEDIUM','estimated_minutes':45,'url':f'https://example.com/canary-{i}'})
m=req(f'/api/coaching/v3/students/{sid}/model?week_start=2026-09-21');assert m['effective_level']=='MEDIUM' and len(m['courses'])==1 and len(m['responsibilities'])==1
req(f'/api/coaching/v2/students/{sid}/dashboard?week_start=2026-09-21')
h=req(f'/api/coaching/v3/students/{sid}/homework/auto','POST',{'week_start':'2026-09-21'});assert h['created']==2
h2=req(f'/api/coaching/v3/students/{sid}/homework/auto','POST',{'week_start':'2026-09-21'});assert h2['created']==0 and len(h2['assignments'])==2
hid=h['assignments'][0]['id'];req(f'/api/coaching/v3/homework/{hid}','PATCH',{'status':'DONE'})
h3=req(f'/api/coaching/v3/students/{sid}/homework/auto','POST',{'week_start':'2026-09-21','replace_unfinished':True});assert len(h3['assignments'])==2 and any(x['id']==hid and x['status']=='DONE' for x in h3['assignments'])
req(f'/api/coaching/v3/students/{sid}/profile','PATCH',{'class_id':cl,'difficulty_override':'HARD'})
assert req(f'/api/coaching/v3/students/{sid}/model')['effective_level']=='HARD'
req('/api/online/internet-test/genesis-audit-invalid-token',expected=404)
req('/api/coaching/v3/resources')
print('GENESIS_V3_CANARY_API_OK checks='+str(checks))
