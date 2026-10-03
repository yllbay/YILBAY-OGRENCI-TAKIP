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
root=Path(os.environ.get('ANA_QA_ROOT','/tmp/recovery/ana-r2-audit'));root.mkdir(parents=True,exist_ok=True)
name='genesis-ana-r2-qa-'+os.environ['GITHUB_RUN_ID'];token=secrets.token_hex(32)
prefix='ANA_PRG/_qa/'+os.environ['GITHUB_RUN_ID']+'-'+secrets.token_hex(8)+'/'
if os.environ.get('GITHUB_ACTIONS')=='true':print('::add-mask::'+token,flush=True)
def cfcall(method,path,*extra):
    r=subprocess.run(['curl','-fsS','--max-time','30','-X',method,
       f'https://api.cloudflare.com/client/v4/accounts/{account}'+path,'-H','Authorization: Bearer '+cf,*extra],capture_output=True,check=True)
    data=json.loads(r.stdout);assert data.get('success'),data.get('errors');return data.get('result')
source=r'''export default {async fetch(request,env){try{
  const headers={'Cache-Control':'no-store','X-ANA-QA':'isolated-r2-v1'};
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
}catch(error){return Response.json({code:error.name,message:error.message},{status:500});}}};'''
(root/'index.mjs').write_text(source)
metadata={'main_module':'index.mjs','compatibility_date':'2026-09-10','compatibility_flags':['global_fetch_strictly_public'],'bindings':[
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
        body=target.read_bytes()
        # A Cloudflare front-door error must not be interpreted as a missing R2
        # object. Log request identity, never tokens or object contents.
        if hs.get('x-ana-qa')!='isolated-r2-v1':
            print('QA_TRANSPORT_RESPONSE',json.dumps({'method':method,'status':status,
                'cf_ray':hs.get('cf-ray'),'body_sha256':hashlib.sha256(body).hexdigest(),
                'error':body.decode(errors='replace')[:80] if body.startswith(b'error code:') else 'unexpected response'}),flush=True)
        return status,body,hs.get('etag')
    class ActualR2:
        def get(self,key):
            # Retry known Cloudflare transport errors on reads only. Their cause
            # is external to the QA handler; never replay an uncertain write.
            for attempt in range(20):
                status,data,etag=request('GET',key)
                if not data.startswith(b'error code:') or not any(e in data for e in (b'1104',b'1042')):break
                time.sleep(1)
            if status==404 and not data:return None,None
            assert status==200,(status,data[:100]);return data,etag
        def put(self,key,value,etag=None,create=False,mime='application/octet-stream'):
            # Include attempted writes in the scoped cleanup manifest.
            owned.add(key)
            # Cloudflare 1042 without our X-ANA-QA marker is a front-door
            # rejection before the QA Worker handler executes. Retrying only that
            # exact pre-handler condition cannot duplicate an accepted R2 write.
            for attempt in range(20):
                status,data,next_etag=request('PUT',key,value,etag,create,mime)
                headers=(root/'headers').read_text(errors='replace').lower()
                pre_handler_1042=(status==404 and data==b'error code: 1042\n' and 'x-ana-qa: isolated-r2-v1' not in headers)
                if not pre_handler_1042:break
                time.sleep(1)
            if status==412:raise RuntimeError('ANA_SNAPSHOT_CONFLICT')
            assert status==200,(status,data[:100]);return next_etag
    # Readiness must exercise the real R2 binding, not merely the Worker handler.
    # A missing isolated object is the safe readiness probe: 404 + our marker proves
    # the request reached this exact Worker and DATA binding without writing anything.
    for _ in range(30):
        status,body,_=request('GET','ANA_PRG/_binding-readiness')
        headers=(root/'headers').read_text(errors='replace').lower()
        if status==404 and body==b'' and 'x-ana-qa: isolated-r2-v1' in headers:break
        time.sleep(1)
    else:raise RuntimeError('QA Worker/R2 binding unavailable')
    assert request('GET','DATA/genesis.db')[0]==400,'Protected namespace was accessible'
    obj=ActualR2();s=Service(Store(root/'first-container',obj))
    cls=s.save('classes',dict(name='Ephemeral real R2 QA'),'QA')
    st=s.save('students',dict(name='Ephemeral student',code='R2_QA',pin='synthetic-pin',class_id=cls['id'],courses=['TYT_MAT']),'QA')
    image=Image.new('RGB',(300,500),'white');b=io.BytesIO();image.save(b,'PNG')
    f=s.upload('synthetic.png','image/png',b.getvalue(),'QA',st['id'],'submissions')
    raw,_=obj.get(f['key']);assert hashlib.sha256(raw).hexdigest()==f['sha256']
    before=s.store.health()['counts']
    restored=Service(Store(root/'cold-container',obj));assert restored.store.restored
    assert restored.store.health()['counts']==before
    assert restored.store.get('students',st['id'])['code']=='R2_QA'
    # Exercise CAS on a disposable object with a deterministically stale ETag.
    # No-op startup transactions intentionally no longer rewrite the DB snapshot,
    # so snapshot ETags must not be made stale by artificial startup writes.
    cas_key='ANA_PRG/_cas-probe.bin'
    first_etag=obj.put(cas_key,b'v1',create=True)
    second_etag=obj.put(cas_key,b'v2',etag=first_etag)
    assert second_etag and second_etag!=first_etag
    try:obj.put(cas_key,b'v3',etag=first_etag)
    except RuntimeError:pass
    else:raise AssertionError('Stale ETag overwrote CAS probe')
    db,_=obj.get(SNAPSHOT_KEY);assert db.startswith(b'SQLite format 3')
    report=dict(ok=True,adapter='actual Cloudflare Worker R2 binding',isolated_prefix=prefix,
       restored=True,counts=before,file_sha256=f['sha256'],conditional_conflict=True,
       protected_namespace_denied=True,source_files_imported=0,objects=[dict(key=prefix+k) for k in sorted(owned)])
    report_path=Path(os.environ.get('ANA_QA_REPORT','/tmp/recovery/snapshot/ana-actual-r2-acceptance.json'))
    report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2))
    print('ANA_ACTUAL_R2_HASH_CAS_COLD_RESTORE_PROTECTED_NAMESPACE_PASS',flush=True)
finally:
    if created:
        cleanup_errors=[]
        try:
            for key in owned:
                assert key.startswith('ANA_PRG/')
                status,_,_=request('DELETE',key)
                if status!=204:cleanup_errors.append(key)
        finally:cfcall('DELETE','/workers/scripts/'+name)
        assert not cleanup_errors,('Scoped QA cleanup needs attention',cleanup_errors)
        print('Ephemeral ANA-only R2 fixtures and expiring QA Worker removed',flush=True)
