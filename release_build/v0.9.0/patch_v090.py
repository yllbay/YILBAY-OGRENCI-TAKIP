from pathlib import Path
import json,re
ROOT=Path('/tmp/yilbay090')
app=ROOT/'app/public/app.js'
server=ROOT/'app/server.js'

a=app.read_text(encoding='utf-8')
s=server.read_text(encoding='utf-8')

for old in ['0.8.2']:
    a=a.replace(old,'0.9.0')
    s=s.replace(old,'0.9.0')
(ROOT/'app/VERSION').write_text('0.9.0\n',encoding='utf-8')

# Frontend: Drive panel
old=''' <div class="section"><button class="btn primary" onclick="integrationSettingsModal()">API Ayarlarını Aç</button></div>`'''
new=''' <div class="section"><div class="section-head"><h2>Google Drive Kaynak Havuzu</h2><span class="muted">Salt-okunur bağlantı</span></div><div id="drivePanel"><div class="card">Drive durumu okunuyor…</div></div></div>\n  <div class="section"><button class="btn primary" onclick="integrationSettingsModal()">API Ayarlarını Aç</button></div>`'''
if old not in a: raise SystemExit('integrations insert point not found')
a=a.replace(old,new,1)

marker='window.integrationSettingsModal='
pos=a.find(marker)
if pos<0: raise SystemExit('settings modal marker missing')
pre=a[:pos]; idx=pre.rfind('\n}\n')
if idx<0: raise SystemExit('load status end missing')
pre=pre[:idx]+'\n  loadDriveStatus();'+pre[idx:]
a=pre+a[pos:]

needle='<div class="field" style="grid-column:1/-1"><label>YouTube Data API Key</label><input id="youtubeKey" type="password" autocomplete="off" placeholder="AIza..."></div>'
repl=needle+'<div class="field"><label>Google Drive OAuth Client ID</label><input id="driveClientId" autocomplete="off" placeholder="...apps.googleusercontent.com"></div><div class="field"><label>Google Drive OAuth Client Secret</label><input id="driveClientSecret" type="password" autocomplete="off" placeholder="GOCSPX-..."></div><div class="field" style="grid-column:1/-1"><label>Google Drive Kaynak Klasörü ID</label><input id="driveFolderId" autocomplete="off" placeholder="Drive klasör ID"></div>'
if needle not in a: raise SystemExit('settings fields marker missing')
a=a.replace(needle,repl,1)

needle='''  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;\n  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;\n  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});'''
repl='''  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;\n  const driveClientId=q("driveClientId").value.trim(),driveClientSecret=q("driveClientSecret").value.trim(),driveFolderId=q("driveFolderId").value.trim();\n  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;\n  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",driveClientId:driveClientId||"__KEEP__",driveClientSecret:driveClientSecret||"__KEEP__",driveFolderId:driveFolderId||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});'''
if needle not in a: raise SystemExit('save settings marker missing')
a=a.replace(needle,repl,1)

frontend_add=r'''
async function loadDriveStatus(){const el=q("drivePanel");if(!el)return;try{const d=await apiJson("/api/drive/status");el.innerHTML=`<div class="integration-grid"><div class="card integration-card"><div class="integration-head"><div><div class="cell-title">Google Drive</div><div class="cell-sub">PDF kaynak havuzu · drive.readonly</div></div><span class="badge ${d.connected?"good":d.configured?"mid":"neutral"}">${d.connected?"Bağlı":d.configured?"Yetkilendirme gerekli":"OAuth ayarı gerekli"}</span></div><div class="integration-meta">Klasör: <b>${d.folderConfigured?"Ayarlı":"Ayarlanmamış"}</b></div><div class="toolbar-group" style="margin-top:12px">${d.configured&&!d.connected?`<button class="btn primary" onclick="connectGoogleDrive()">Google Drive'a Bağlan</button>`:""}${d.connected?`<button class="btn primary" onclick="indexGoogleDrive()">PDF'leri İndeksle</button><button class="btn ghost" onclick="disconnectGoogleDrive()">Bağlantıyı Kes</button>`:""}</div></div></div>`}catch(e){el.innerHTML=`<div class="notice error">Drive durumu okunamadı: ${e.message}</div>`}}
window.connectGoogleDrive=async()=>{try{const d=await apiJson("/api/drive/oauth/start",{});window.open(d.authorizationUrl,"_blank","noopener");alert("Google yetkilendirme ekranı açıldı. Onaydan sonra bu sayfaya dönün.");setTimeout(loadDriveStatus,2500)}catch(e){alert("Drive bağlantısı başlatılamadı: "+e.message)}}
window.disconnectGoogleDrive=async()=>{if(!confirm("Google Drive bağlantısı kesilsin mi?"))return;try{await apiJson("/api/drive/disconnect",{});loadDriveStatus()}catch(e){alert("Drive bağlantısı kesilemedi: "+e.message)}}
window.indexGoogleDrive=async()=>{try{const d=await apiJson("/api/drive/index",{});let added=0,updated=0;for(const x of d.items||[]){if(!x.matched)continue;const existing=db.resources.find(r=>r.driveFileId===x.id);const next={type:"PDF",course:x.course,topic:x.topic,level:x.level,title:x.title||x.name,url:x.webViewLink||"",driveFileId:x.id,driveModifiedTime:x.modifiedTime||null,driveSource:true};if(existing){Object.assign(existing,next);updated++}else{db.resources.push({id:Date.now()+added,...next});added++}}save();loadDriveStatus();alert(`Drive indeksleme tamamlandı.\nEşleşen: ${d.matchedCount||0}\nMetadata gerekli: ${d.unmatchedCount||0}\nYeni kaynak: ${added}\nGüncellenen: ${updated}`)}catch(e){alert("Drive indeksleme başarısız: "+e.message)}}
'''
idx=a.rfind('dashboard();')
if idx<0: raise SystemExit('frontend bootstrap marker missing')
a=a[:idx]+frontend_add+'\n'+a[idx:]

needle='''    youtubeApiKey:String(next.youtubeApiKey||"").trim(),\n    openaiModel:String(next.openaiModel||"gpt-5.6-luna").trim()||"gpt-5.6-luna",'''
repl='''    youtubeApiKey:String(next.youtubeApiKey||"").trim(),\n    driveClientId:String(next.driveClientId||"").trim(),\n    driveClientSecret:String(next.driveClientSecret||"").trim(),\n    driveFolderId:String(next.driveFolderId||"").trim(),\n    driveRefreshToken:String(next.driveRefreshToken||"").trim(),\n    driveAccessToken:String(next.driveAccessToken||"").trim(),\n    driveAccessTokenExpiresAt:Number(next.driveAccessTokenExpiresAt||0)||0,\n    driveOauthState:String(next.driveOauthState||"").trim(),\n    openaiModel:String(next.openaiModel||"gpt-5.6-luna").trim()||"gpt-5.6-luna",'''
if needle not in s: raise SystemExit('writeSecrets marker missing')
s=s.replace(needle,repl,1)

needle='''    drive:{configured:false,mode:"resource-metadata"},'''
repl='''    drive:{configured:!!(s.driveClientId&&s.driveClientSecret),connected:!!s.driveRefreshToken,folderConfigured:!!s.driveFolderId,mode:"oauth-readonly"},'''
if needle not in s: raise SystemExit('drive status marker missing')
s=s.replace(needle,repl,1)

old_handler='''      const b=await readJson(req,128*1024),old=readStoredSecrets();\n      writeSecrets({\n        openaiApiKey:b.openaiApiKey==="__KEEP__"?old.openaiApiKey:b.openaiApiKey,\n        youtubeApiKey:b.youtubeApiKey==="__KEEP__"?old.youtubeApiKey:b.youtubeApiKey,\n        openaiModel:b.openaiModel||old.openaiModel||"gpt-5.6-luna",\n        usdTry:b.usdTry??old.usdTry??48.12,\n        monthlyBudgetTry:b.monthlyBudgetTry??old.monthlyBudgetTry??1000\n      });'''
new_handler='''      const b=await readJson(req,128*1024),old=readStoredSecrets();\n      writeSecrets({\n        ...old,\n        openaiApiKey:b.openaiApiKey==="__KEEP__"?old.openaiApiKey:b.openaiApiKey,\n        youtubeApiKey:b.youtubeApiKey==="__KEEP__"?old.youtubeApiKey:b.youtubeApiKey,\n        driveClientId:b.driveClientId==="__KEEP__"?old.driveClientId:b.driveClientId,\n        driveClientSecret:b.driveClientSecret==="__KEEP__"?old.driveClientSecret:b.driveClientSecret,\n        driveFolderId:b.driveFolderId==="__KEEP__"?old.driveFolderId:b.driveFolderId,\n        openaiModel:b.openaiModel||old.openaiModel||"gpt-5.6-luna",\n        usdTry:b.usdTry??old.usdTry??48.12,\n        monthlyBudgetTry:b.monthlyBudgetTry??old.monthlyBudgetTry??1000\n      });'''
if old_handler not in s: raise SystemExit('settings handler marker missing')
s=s.replace(old_handler,new_handler,1)

backend_add=r'''
function driveRedirectUri(){return `http://127.0.0.1:${port}/api/drive/oauth/callback`}
function driveTokenSavePatch(patch){const old=readStoredSecrets();return writeSecrets({...old,...patch})}
async function driveRefreshAccessToken(){const st=readStoredSecrets();if(st.driveAccessToken&&Number(st.driveAccessTokenExpiresAt||0)>Date.now()+60000)return st.driveAccessToken;if(!st.driveRefreshToken)throw new Error("Google Drive yetkilendirmesi yok");const body=new URLSearchParams({client_id:st.driveClientId,client_secret:st.driveClientSecret,refresh_token:st.driveRefreshToken,grant_type:"refresh_token"});const r=await fetch("https://oauth2.googleapis.com/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error_description||j.error||`Google token HTTP ${r.status}`);driveTokenSavePatch({driveAccessToken:j.access_token,driveAccessTokenExpiresAt:Date.now()+Math.max(60,Number(j.expires_in||3600))*1000});return j.access_token}
function driveMetadataFromFile(file){const ap=file.appProperties||{};let course=String(ap.yilbayCourse||"").trim(),topic=String(ap.yilbayTopic||"").trim(),level=String(ap.yilbayLevel||"").trim(),title=String(ap.yilbayTitle||"").trim();if(!(course&&topic&&level)){const base=String(file.name||"").replace(/\.pdf$/i,"");const parts=base.split("__").map(x=>x.trim()).filter(Boolean);if(parts.length>=4){course=course||parts[0];topic=topic||parts[1];level=level||parts[2];title=title||parts.slice(3).join("__")}}return {course,topic,level,title:title||String(file.name||"").replace(/\.pdf$/i,""),matched:!!(course&&topic&&level)}}
async function driveListPdfIndex(){const st=readStoredSecrets();if(!st.driveFolderId)throw new Error("Google Drive kaynak klasörü ayarlanmamış");const token=await driveRefreshAccessToken();let pageToken="",files=[];do{const q=`'${String(st.driveFolderId).replace(/'/g,"\\'")}' in parents and mimeType='application/pdf' and trashed=false`;const u=new URL("https://www.googleapis.com/drive/v3/files");u.searchParams.set("q",q);u.searchParams.set("pageSize","1000");u.searchParams.set("fields","nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink,appProperties)");if(pageToken)u.searchParams.set("pageToken",pageToken);const r=await fetch(u,{headers:{Authorization:`Bearer ${token}`}});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error?.message||`Drive API HTTP ${r.status}`);files.push(...(j.files||[]));pageToken=j.nextPageToken||""}while(pageToken);return files.map(f=>({...f,...driveMetadataFromFile(f)}))}
async function handleDriveOauthStart(req,res){const st=readStoredSecrets();if(!(st.driveClientId&&st.driveClientSecret))return json(res,400,{ok:false,error:"Google Drive OAuth Client ID/Secret ayarlanmamış"});const state=require("crypto").randomBytes(20).toString("hex");driveTokenSavePatch({driveOauthState:state});const u=new URL("https://accounts.google.com/o/oauth2/v2/auth");u.searchParams.set("client_id",st.driveClientId);u.searchParams.set("redirect_uri",driveRedirectUri());u.searchParams.set("response_type","code");u.searchParams.set("scope","https://www.googleapis.com/auth/drive.readonly");u.searchParams.set("access_type","offline");u.searchParams.set("prompt","consent");u.searchParams.set("state",state);return json(res,200,{ok:true,authorizationUrl:u.toString(),redirectUri:driveRedirectUri()})}
async function handleDriveOauthCallback(u,res){const st=readStoredSecrets();if(!u.searchParams.get("code")||u.searchParams.get("state")!==st.driveOauthState){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"});return res.end("<h2>Google Drive yetkilendirmesi doğrulanamadı.</h2>")}const body=new URLSearchParams({code:u.searchParams.get("code"),client_id:st.driveClientId,client_secret:st.driveClientSecret,redirect_uri:driveRedirectUri(),grant_type:"authorization_code"});const r=await fetch("https://oauth2.googleapis.com/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body});const j=await r.json().catch(()=>({}));if(!r.ok){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"});return res.end("<h2>Google Drive bağlantısı tamamlanamadı.</h2>")}driveTokenSavePatch({driveRefreshToken:j.refresh_token||st.driveRefreshToken||"",driveAccessToken:j.access_token||"",driveAccessTokenExpiresAt:Date.now()+Math.max(60,Number(j.expires_in||3600))*1000,driveOauthState:""});res.writeHead(200,{"Content-Type":"text/html; charset=utf-8"});res.end("<h2>Google Drive bağlandı.</h2><p>Bu pencereyi kapatıp YILBAY uygulamasına dönebilirsiniz.</p>")}
async function handleDriveIndex(req,res){const items=await driveListPdfIndex();return json(res,200,{ok:true,items,matchedCount:items.filter(x=>x.matched).length,unmatchedCount:items.filter(x=>!x.matched).length})}
'''
route_marker='http.createServer(async(req,res)=>{'
ri=s.find(route_marker)
if ri<0: raise SystemExit('server route marker missing')
s=s[:ri]+backend_add+'\n'+s[ri:]

needle='''    if(u.pathname==="/api/ai/costs"&&req.method==="GET") return json(res,200,{ok:true,...costSummary()});'''
repl=needle+'''\n    if(u.pathname==="/api/drive/status"&&req.method==="GET"){const d=integrationStatus().drive;return json(res,200,{ok:true,...d})}\n    if(u.pathname==="/api/drive/oauth/start"&&req.method==="POST") return await handleDriveOauthStart(req,res);\n    if(u.pathname==="/api/drive/oauth/callback"&&req.method==="GET") return await handleDriveOauthCallback(u,res);\n    if(u.pathname==="/api/drive/index"&&req.method==="POST") return await handleDriveIndex(req,res);\n    if(u.pathname==="/api/drive/disconnect"&&req.method==="POST"){const old=readStoredSecrets();writeSecrets({...old,driveRefreshToken:"",driveAccessToken:"",driveAccessTokenExpiresAt:0,driveOauthState:""});return json(res,200,{ok:true})}'''
if needle not in s: raise SystemExit('route insertion marker missing')
s=s.replace(needle,repl,1)

app.write_text(a,encoding='utf-8')
server.write_text(s,encoding='utf-8')
print('PATCH090_OK')
