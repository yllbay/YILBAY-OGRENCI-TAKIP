"""Real R2 acceptance, isolated random ANA test namespace; no GENESIS data access.

Uses an expiring, authenticated temporary Worker with native R2 binding. This
proves actual remote object/CAS/SQLite restore semantics, separately from the
container's S3 provider connection, which is checked by production health.
"""
import hashlib,io,json,os,secrets,subprocess,tempfile,time,urllib.parse
from pathlib import Path
from PIL import Image
from ana_prg.storage import Store,SNAPSHOT_KEY
from ana_prg.service import Service
account=os.environ['CLOUDFLARE_ACCOUNT_ID'].strip();cf=os.environ['CLOUDFLARE_API_TOKEN']
root=Path('/tmp/recovery/ana-r2-audit');root.mkdir(parents=True,exist_ok=True)
name='genesis-ana-r2-qa-'+os.environ['GITHUB_RUN_ID'];token=secrets.token_hex(32)
prefix='ANA_PRG/_qa/'+os.environ['GITHUB_RUN_ID']+'-'+secrets.token_hex(8)+'/'
print('::add-mask::'+token,flush=True)
def cfcall(method,path,*extra):
    r=subprocess.run(['curl','-fsS','--max-time','30','-X',method,
       f'https://api.cloudflare.com/client/v4/accounts/{account}'+path,'-H','Authorization: Bearer '+cf,*extra],capture_output=True,check=True)
    data=json.loads(r.stdout);assert data.get('success'),data.get('errors');return data.get('result')
source=r'''export default {async fetch(request,env){
  const headers={'Cache-Control':'no-store'};
  if(Date.now()/1000>Number(env.EXPIRES)||request.headers.get('Authorization')!=='Bearer '+env.QA_TOKEN)
    return new Response('Denied',{status:403,headers});
  const logical=new URL(request.url).searchParams.get('key')||'';
  if(!logical.startsWith('ANA_PRG/')||logical.includes('..')||logical.includes('\\'))
    return new Response('Namespace denied',{status:400,headers});
  const key=env.QA_PREFIX+logical;
  if(request.method==='GET'){
    const o=await env.DATA.get(key);if(!o)return new Response(null,{status:404,headers});
    return new Response(o.body,{headers:{...headers,ETag:o.httpEtag}});
  }
  if(request.method==='PUT'){
    const bytes=await request.arrayBuffer();if(bytes.byteLength>21*1024*1024)return new Response('Too large',{status:413});
    const cond=new Headers();for(const h of ['if-match','if-none-match'])if(request.headers.has(h))cond.set(h,request.headers.get(h));
    const o=await env.DATA.put(key,bytes,{onlyIf:cond,httpMetadata:{contentType:request.headers.get('Content-Type')||'application/octet-stream'},sha256:request.headers.get('X-SHA256')});
    if(!o)return new Response('Conflict',{status:412,headers});
    return new Response(null,{status:200,headers:{...headers,ETag:o.httpEtag}});
  }
  if(request.method==='DELETE'){await env.DATA.delete(key);return new Response(null,{status:204,headers});}
  return new Response('Method denied',{status:405,headers});
}};'''
(root/'index.mjs').write_text(source)
metadata={'main_module':'index.mjs','compatibility_date':'2026-09-10','bindings':[
 {'name':'DATA','type':'r2_bucket','bucket_name':'genesis-web-0152-data'},
 {'name':'QA_TOKEN','type':'secret_text','text':token},
 {'name':'QA_PREFIX','type':'plain_text','text':prefix},
 {'name':'EXPIRES','type':'plain_text','text':str(int(time.time())+900)}]}
(root/'metadata.json').write_text(json.dumps(metadata));owned=set();created=False
try:
    cfcall('PUT','/workers/scripts/'+name,'-F',f'metadata=@{root}/metadata.json;type=application/json',
           '-F',f'index.mjs=@{root}/index.mjs;type=application/javascript+module');created=True
    cfcall('POST','/workers/scripts/'+name+'/subdomain','-H','Content-Type: application/json','--data','{"enabled":true}')
    subdomain=cfcall('GET','/workers/subdomain')['subdomain'];url=f'https://{name}.{subdomain}.workers.dev/'
    def request(method,key,data=None,etag=None,create=False,mime='application/octet-stream'):
        target=root/'response';headers=root/'headers'
        args=['curl','-sS','--max-time','30','-X',method,url+'?key='+urllib.parse.quote(key,safe=''),
            '-H','Authorization: Bearer '+token,'-o',str(target),'-D',str(headers),'-w','%{http_code}']
        if data is not None:
            (root/'payload').write_bytes(data);args+=['--data-binary','@'+str(root/'payload'),'-H','Content-Type: '+mime,
             '-H','X-SHA256: '+hashlib.sha256(data).hexdigest()]
        if create:args+=['-H','If-None-Match: *']
        if etag:args+=['-H','If-Match: '+etag]
        r=subprocess.run(args,capture_output=True,check=True);status=int(r.stdout)
        hs={a.partition(':')[0].lower():a.partition(':')[2].strip() for a in headers.read_text().splitlines() if ':' in a}
        return status,target.read_bytes(),hs.get('etag')
    class ActualR2:
        def get(self,key):
            status,data,etag=request('GET',key)
            if status==404:return None,None
            assert status==200,(status,data[:100]);return data,etag
        def put(self,key,value,etag=None,create=False,mime='application/octet-stream'):
            status,data,next_etag=request('PUT',key,value,etag,create,mime)
            if status==412:raise RuntimeError('ANA_SNAPSHOT_CONFLICT')
            assert status==200,(status,data[:100]);owned.add(key);return next_etag
    for _ in range(20):
        status,_,_=request('GET',SNAPSHOT_KEY)
        if status==404:break
        time.sleep(1)
    else:raise RuntimeError('QA Worker unavailable')
    assert request('GET','DATA/genesis.db')[0]==400,'Protected namespace was accessible'
    obj=ActualR2();s=Service(Store(root/'first-container',obj))
    cls=s.save('classes',dict(name='Ephemeral real R2 QA'),'QA')
    st=s.save('students',dict(name='Ephemeral student',code='R2_QA',pin='synthetic-pin',class_id=cls['id'],courses=['TYT_MAT']),'QA')
    image=Image.new('RGB',(300,500),'white');b=io.BytesIO();image.save(b,'PNG')
    f=s.upload('synthetic.png','image/png',b.getvalue(),'QA',st['id'],'submissions')
    raw,_=obj.get(f['key']);assert hashlib.sha256(raw).hexdigest()==f['sha256']
    before=s.store.health()['counts'];old_etag=s.store.etag
    restored=Service(Store(root/'cold-container',obj));assert restored.store.restored
    assert restored.store.health()['counts']==before
    assert restored.store.get('students',st['id'])['code']=='R2_QA'
    try:obj.put(SNAPSHOT_KEY,b'not-a-database',etag=old_etag)
    except RuntimeError:pass
    else:raise AssertionError('Stale ETag overwrote snapshot')
    db,_=obj.get(SNAPSHOT_KEY);assert db.startswith(b'SQLite format 3')
    report=dict(ok=True,adapter='actual Cloudflare Worker R2 binding',isolated_prefix=prefix,
       restored=True,counts=before,file_sha256=f['sha256'],conditional_conflict=True,
       protected_namespace_denied=True,source_files_imported=0,objects=[dict(key=prefix+k) for k in sorted(owned)])
    Path('/tmp/recovery/snapshot/ana-actual-r2-acceptance.json').write_text(json.dumps(report,indent=2))
    print('ANA_ACTUAL_R2_HASH_CAS_COLD_RESTORE_PROTECTED_NAMESPACE_PASS',flush=True)
finally:
    if created:
        for key in owned:
            assert key.startswith('ANA_PRG/')
            status,_,_=request('DELETE',key);assert status==204
        cfcall('DELETE','/workers/scripts/'+name)
        print('Ephemeral ANA-only R2 fixtures and expiring QA Worker removed',flush=True)
