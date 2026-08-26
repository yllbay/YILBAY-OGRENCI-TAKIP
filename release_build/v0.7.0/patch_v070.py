from pathlib import Path
import re

root=Path('/tmp/yilbay070')
server=root/'app/server.js'
appjs=root/'app/public/app.js'
version=root/'VERSION'

s=server.read_text(encoding='utf-8')
# version
s=s.replace('version:"0.6.8"','version:"0.7.0"')

# Remove PowerShell credential probing entirely. Environment/manual only.
pat=r'let credentialCache=\{at:0,value:null\};.*?function readSecrets\(\)\{'
rep='''function readWindowsCredential(){\n  return {value:null,diagnostic:{method:"disabled-environment-mode",found:false,userMatch:false,targetMatched:false}};\n}\nfunction readSecrets(){'''
s,n=re.subn(pat,rep,s,flags=re.S)
if n!=1: raise SystemExit(f'credential block patch count={n}')

# Replace secret selection so environment is first and no credential call is made.
pat=r'function readSecrets\(\)\{.*?\n\}'
old_match=re.search(pat,s,flags=re.S)
if not old_match: raise SystemExit('readSecrets not found')
new_read='''function readSecrets(){\n  const stored=readStoredSecrets();\n  const envKey=String(process.env.OPENAI_API_KEY||"").trim();\n  const manual=String(stored.openaiApiKey||"").trim();\n  let openaiApiKey="",openaiApiSource="none";\n  if(envKey){ openaiApiKey=envKey; openaiApiSource="environment"; }\n  else if(manual){ openaiApiKey=manual; openaiApiSource="manual"; }\n  return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:{method:"disabled-environment-mode",found:false,userMatch:false,targetMatched:false}};\n}'''
s=s[:old_match.start()]+new_read+s[old_match.end():]

# Capacity-aware deterministic term planner with nearest-level resource matching.
pat=r'function deterministicPlan\(student,curriculum,resources=\[\]\)\{.*?\n\}\nasync function handleAiPlan'
new_plan=r'''function deterministicPlan(student,curriculum,resources=[]){
  const topics=flattenCurriculum(curriculum,student.courses);
  const start=new Date(student.registeredAt||new Date().toISOString().slice(0,10));
  const end=new Date(student.courseEndDate||start);
  const weekMs=7*864e5;
  const weekCount=Math.max(1,Math.floor((end-start)/weekMs)+1);
  const studyDays=Math.max(1,Math.min(7,Number(student.weeklyStudyDays||6)));
  const dailyMinutes=Math.max(30,Number(student.dailyMinutes||120));
  const weeklyCapacity=studyDays*dailyMinutes;
  const levelOrder=["Başlangıç","Kolay","Orta","Orta-Zor","Zor","İleri"];
  function pickResource(course,topic,wanted){
    const same=resources.filter(r=>r.course===course&&r.topic===topic);
    if(!same.length) return null;
    const wi=Math.max(0,levelOrder.indexOf(wanted));
    same.sort((a,b)=>{
      const ai=levelOrder.indexOf(a.level),bi=levelOrder.indexOf(b.level);
      const ad=ai<0?99:Math.abs(ai-wi),bd=bi<0?99:Math.abs(bi-wi);
      return ad-bd;
    });
    return same[0];
  }
  const weeks=Array.from({length:weekCount},(_,i)=>({week:i+1,startDate:new Date(start.getTime()+i*weekMs).toISOString().slice(0,10),capacityMinutes:weeklyCapacity,plannedMinutes:0,items:[]}));
  const baseTopicMinutes=Math.min(120,Math.max(35,Math.round(dailyMinutes*0.55)));
  let wi=0,overflowTopics=[];
  for(const x of topics){
    const level=student.levels?.[x.course]||"Orta";
    const res=pickResource(x.course,x.topic,level);
    const estimatedMinutes=baseTopicMinutes;
    while(wi<weeks.length && weeks[wi].plannedMinutes+estimatedMinutes>weeks[wi].capacityMinutes) wi++;
    if(wi>=weeks.length){overflowTopics.push({...x,estimatedMinutes});continue}
    weeks[wi].items.push({...x,type:"Yeni Konu",priority:"normal",resourceId:res?.id??null,resourceTitle:res?.title||null,resourceLevel:res?.level||null,studentLevel:level,estimatedMinutes});
    weeks[wi].plannedMinutes+=estimatedMinutes;
  }
  const totalCapacityMinutes=weekCount*weeklyCapacity;
  const requiredMinutes=topics.length*baseTopicMinutes;
  return {mode:"deterministic",weeks,totalTopics:topics.length,weeklyCapacityMinutes:weeklyCapacity,totalCapacityMinutes,requiredMinutes,overload:overflowTopics.length>0,overflowCount:overflowTopics.length,overflowTopics};
}
async function handleAiPlan'''
s,n=re.subn(pat,new_plan,s,flags=re.S)
if n!=1: raise SystemExit(f'deterministicPlan patch count={n}')

# Add a real OpenAI connection test endpoint with cost tracking.
anchor='function flattenCurriculum(curriculum,courses){'
ping=r'''async function handleAiPing(req,res){
  const status=integrationStatus();
  if(!status.openai.configured) return json(res,400,{ok:false,error:"OpenAI API anahtarı bağlı değil"});
  const started=Date.now();
  const ai=await openaiRequest({instructions:"Yalnızca OK yaz.",input:"Bağlantı testi",reasoning:"low"});
  const cost=appendUsage("connection_test",ai.model,ai.data?.usage||{},{});
  return json(res,200,{ok:true,connected:true,model:ai.model,latencyMs:Date.now()-started,response:String(ai.text||"").trim().slice(0,80),usage:ai.data?.usage||null,cost});
}
'''
if anchor not in s: raise SystemExit('flattenCurriculum anchor missing')
s=s.replace(anchor,ping+anchor,1)

route='if(u.pathname==="/api/ai/plan"&&req.method==="POST") return await handleAiPlan(req,res);'
if route not in s: raise SystemExit('route anchor missing')
s=s.replace(route,'if(u.pathname==="/api/ai/ping"&&req.method==="POST") return await handleAiPing(req,res);\n    '+route,1)

# Assert PowerShell process invocation is gone from server code.
if 'powershell.exe' in s.lower(): raise SystemExit('powershell.exe still present in server.js')
server.write_text(s,encoding='utf-8')

# UI
j=appjs.read_text(encoding='utf-8')
j=j.replace('<span class="version">v0.6.1</span>','<span class="version">v0.7.0</span>')
# Add connection-test action in integrations page head.
old='pageHead("AI ve API Entegrasyonları","OpenAI ile adaptif planlama/ödev analizi, YouTube ile konu anlatım videosu seçimi. API anahtarları tarayıcıya kaydedilmez.")'
new='pageHead("AI ve API Entegrasyonları","OpenAI ile adaptif planlama/ödev analizi, YouTube ile konu anlatım videosu seçimi. API anahtarları tarayıcıya kaydedilmez.",`<button class="btn primary" onclick="testOpenAIConnection()">OpenAI Bağlantısını Test Et</button>`)'
if old not in j: raise SystemExit('integrations pageHead anchor missing')
j=j.replace(old,new,1)

# Inject client test function before generateAiMasterPlan.
anchor='window.generateAiMasterPlan=async()=>{'
client_ping=r'''window.testOpenAIConnection=async()=>{
 const btn=[...document.querySelectorAll("button")].find(x=>x.textContent.includes("OpenAI Bağlantısını Test Et"));
 const old=btn?.textContent;if(btn){btn.disabled=true;btn.textContent="Test ediliyor…"}
 try{
  const r=await apiJson("/api/ai/ping",{});
  alert(`OpenAI bağlantısı başarılı.\nModel: ${r.model}\nGecikme: ${r.latencyMs} ms${r.cost?`\nMaliyet: ${Number(r.cost.try||0).toFixed(4)} TL`:""}`);
  loadIntegrationStatus();
 }catch(e){alert("OpenAI bağlantı testi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent=old||"OpenAI Bağlantısını Test Et"}}
}
'''
if anchor not in j: raise SystemExit('generateAiMasterPlan anchor missing')
j=j.replace(anchor,client_ping+anchor,1)

# Enrich term plan notice with capacity status when deterministic/fallback data is present.
needle='${db.aiPlans?.[key]?`<br><b>AI dönem planı:</b> ${db.aiPlans[key].usedAi?"OpenAI ile üretildi":"kural tabanlı fallback"} · ${db.aiPlans[key].plan?.weeks?.length||0} hafta`:""}'
replacement='${db.aiPlans?.[key]?`<br><b>Dönem planı:</b> ${db.aiPlans[key].usedAi?"OpenAI ile üretildi":"kural tabanlı fallback"} · ${db.aiPlans[key].plan?.weeks?.length||0} hafta${db.aiPlans[key].plan?.weeklyCapacityMinutes?` · haftalık kapasite ${db.aiPlans[key].plan.weeklyCapacityMinutes} dk`:""}${db.aiPlans[key].plan?.overload?` · <span class="badge low">${db.aiPlans[key].plan.overflowCount} konu kapasite dışı</span>`:""}`:""}'
if needle in j: j=j.replace(needle,replacement,1)

appjs.write_text(j,encoding='utf-8')
version.write_text('0.7.0\n',encoding='utf-8')
print('patched v0.7.0')
