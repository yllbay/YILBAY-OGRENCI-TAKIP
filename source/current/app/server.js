const http=require("http"),fs=require("fs"),path=require("path"),cp=require("child_process");
const port=Number(process.env.PORT||43127), pub=path.join(__dirname,"public");
const root=path.resolve(__dirname,"..");
const runtime=path.join(root,"runtime");
const secretFile=path.join(runtime,"api_secrets.json");
const usageFile=path.join(runtime,"ai_usage.jsonl");
fs.mkdirSync(runtime,{recursive:true});

const OPENAI_CREDENTIAL_TARGET="YILBAY-OPENAI-API-HOME";
const OPENAI_CREDENTIAL_USERNAME="YILBAY-DEVELOPMENT-HOME";
let credentialCache={at:0,value:null};
function readStoredSecrets(){
  try{return JSON.parse(fs.readFileSync(secretFile,"utf8"))}catch{return {}}
}
function readWindowsCredential(target=OPENAI_CREDENTIAL_TARGET){
  if(process.platform!=="win32") return {value:null,diagnostic:{method:"not-windows",found:false,userMatch:false}};
  const now=Date.now();
  if(now-credentialCache.at<30000) return credentialCache.value;
  const ps=`$ErrorActionPreference='Stop'
$src=@'
using System;
using System.Runtime.InteropServices;
public static class YilbayCredNative {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
  public struct CREDENTIAL {
    public UInt32 Flags; public UInt32 Type; public IntPtr TargetName; public IntPtr Comment;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
    public UInt32 CredentialBlobSize; public IntPtr CredentialBlob; public UInt32 Persist;
    public UInt32 AttributeCount; public IntPtr Attributes; public IntPtr TargetAlias; public IntPtr UserName;
  }
  [DllImport("advapi32.dll", EntryPoint="CredReadW", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredRead(string target, UInt32 type, UInt32 reservedFlag, out IntPtr credentialPtr);
  [DllImport("advapi32.dll", EntryPoint="CredEnumerateW", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool CredEnumerate(string filter, UInt32 flags, out UInt32 count, out IntPtr credentials);
  [DllImport("advapi32.dll", SetLastError=true)] public static extern void CredFree(IntPtr credentialPtr);
}
'@
Add-Type -TypeDefinition $src -ErrorAction SilentlyContinue
function Convert-Cred([IntPtr]$p,[string]$method){
  $c=[Runtime.InteropServices.Marshal]::PtrToStructure($p,[type][YilbayCredNative+CREDENTIAL])
  $t=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.TargetName)
  $u=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.UserName)
  $bytes=New-Object byte[] $c.CredentialBlobSize
  if($c.CredentialBlobSize -gt 0){[Runtime.InteropServices.Marshal]::Copy($c.CredentialBlob,$bytes,0,$c.CredentialBlobSize)}
  $secret=[Text.Encoding]::Unicode.GetString($bytes).Trim([char]0)
  if([string]::IsNullOrWhiteSpace($secret) -or $secret.Contains([char]0)){$secret=[Text.Encoding]::UTF8.GetString($bytes).Trim([char]0)}
  [pscustomobject]@{target=$t;username=$u;secret=$secret;method=$method}
}
$p=[IntPtr]::Zero
if([YilbayCredNative]::CredRead('${target.replace(/'/g,"''")}',1,0,[ref]$p)){
  try{Convert-Cred $p 'direct'}finally{[YilbayCredNative]::CredFree($p)}
  exit 0
}
$count=0;$arr=[IntPtr]::Zero
if([YilbayCredNative]::CredEnumerate($null,0,[ref]$count,[ref]$arr)){
  try{
    for($i=0;$i -lt $count;$i++){
      $cp=[Runtime.InteropServices.Marshal]::ReadIntPtr($arr,$i*[IntPtr]::Size)
      $c=[Runtime.InteropServices.Marshal]::PtrToStructure($cp,[type][YilbayCredNative+CREDENTIAL])
      $t=[Runtime.InteropServices.Marshal]::PtrToStringUni($c.TargetName)
      if($t -eq '${target.replace(/'/g,"''")}' -or $t.EndsWith('${target.replace(/'/g,"''")}')){Convert-Cred $cp 'enumerate'; exit 0}
    }
  }finally{[YilbayCredNative]::CredFree($arr)}
}
exit 3`;
  try{
    const encoded=Buffer.from(ps,"utf16le").toString("base64");
    const out=cp.execFileSync("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-EncodedCommand",encoded],{encoding:"utf8",windowsHide:true,timeout:7000,stdio:["ignore","pipe","ignore"]}).trim();
    const parsed=JSON.parse(out||"null");
    const user=String(parsed?.username||""); const secret=String(parsed?.secret||"");
    const userMatch=!OPENAI_CREDENTIAL_USERNAME||user===OPENAI_CREDENTIAL_USERNAME;
    const result={value:(secret&&userMatch)?{username:user,secret}:null,diagnostic:{method:String(parsed?.method||"unknown"),found:!!secret,userMatch,targetMatched:String(parsed?.target||"").endsWith(target)}};
    credentialCache={at:now,value:result}; return result;
  }catch{
    const result={value:null,diagnostic:{method:"not-found",found:false,userMatch:false,targetMatched:false}};
    credentialCache={at:now,value:result}; return result;
  }
}
function readSecrets(){
  const stored=readStoredSecrets();
  const credResult=readWindowsCredential();
  const cred=credResult.value;
  const envKey=String(process.env.OPENAI_API_KEY||"").trim();
  const manual=String(stored.openaiApiKey||"").trim();
  let openaiApiKey="",openaiApiSource="none";
  if(cred?.secret && (!OPENAI_CREDENTIAL_USERNAME || cred.username===OPENAI_CREDENTIAL_USERNAME)){
    openaiApiKey=cred.secret; openaiApiSource="windows-credential-manager";
  }else if(envKey){ openaiApiKey=envKey; openaiApiSource="environment"; }
  else if(manual){ openaiApiKey=manual; openaiApiSource="manual"; }
  return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:credResult.diagnostic};
}
function writeSecrets(next){
  const clean={
    openaiApiKey:String(next.openaiApiKey||"").trim(),
    youtubeApiKey:String(next.youtubeApiKey||"").trim(),
    openaiModel:String(next.openaiModel||"gpt-5.6-luna").trim()||"gpt-5.6-luna",
    usdTry:Number(next.usdTry||48.12)||48.12,
    monthlyBudgetTry:Number(next.monthlyBudgetTry||1000)||1000
  };
  fs.writeFileSync(secretFile,JSON.stringify(clean,null,2),"utf8");
  return clean;
}
function integrationStatus(){
  const s=readSecrets();
  return {
    openai:{configured:!!s.openaiApiKey,model:s.openaiModel||"gpt-5.6-luna",source:s.openaiApiSource||"none",credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:s.credentialDiagnostic||null},
    youtube:{configured:!!s.youtubeApiKey},
    drive:{configured:false,mode:"resource-metadata"},
    cost:{usdTry:Number(s.usdTry||48.12)||48.12,monthlyBudgetTry:Number(s.monthlyBudgetTry||1000)||1000}
  };
}

const OPENAI_PRICES={
  "gpt-5.6-luna":{input:0.20,cached:0.02,output:1.20},
  "gpt-5.6-terra":{input:2.00,cached:0.20,output:12.00},
  "gpt-5.6-sol":{input:4.00,cached:0.40,output:20.00}
};
function usageNumbers(usage={}){
  const input=Number(usage.input_tokens||0);
  const output=Number(usage.output_tokens||0);
  const cached=Number(usage.input_tokens_details?.cached_tokens||0);
  return {input,output,cached,uncached:Math.max(0,input-cached)};
}
function estimateCost(model,usage={}){
  const p=OPENAI_PRICES[model]||OPENAI_PRICES["gpt-5.6-luna"];
  const u=usageNumbers(usage);
  const usd=(u.uncached*p.input+u.cached*p.cached+u.output*p.output)/1_000_000;
  const fx=integrationStatus().cost.usdTry;
  return {...u,usd,try:usd*fx};
}
function appendUsage(operation,model,usage,meta={}){
  try{
    const cost=estimateCost(model,usage);
    const row={ts:new Date().toISOString(),operation,model,...cost,meta};
    fs.appendFileSync(usageFile,JSON.stringify(row)+"\n","utf8");
    return row;
  }catch{return null}
}
function readUsageRows(){
  try{
    return fs.readFileSync(usageFile,"utf8").split(/\r?\n/).filter(Boolean).map(x=>JSON.parse(x));
  }catch{return []}
}
function costSummary(){
  const rows=readUsageRows(), now=new Date(), ym=now.toISOString().slice(0,7);
  const month=rows.filter(r=>String(r.ts||"").slice(0,7)===ym);
  const sum=a=>a.reduce((n,r)=>n+Number(r.try||0),0);
  const byOperation={};
  for(const r of month) byOperation[r.operation]=(byOperation[r.operation]||0)+Number(r.try||0);
  const totalTry=sum(month), cfg=integrationStatus().cost;
  return {
    month:ym,
    totalTry,
    totalUsd:month.reduce((n,r)=>n+Number(r.usd||0),0),
    operations:month.length,
    averageTry:month.length?totalTry/month.length:0,
    byOperation,
    budgetTry:cfg.monthlyBudgetTry,
    remainingTry:Math.max(0,cfg.monthlyBudgetTry-totalTry),
    budgetPercent:cfg.monthlyBudgetTry?Math.min(999,100*totalTry/cfg.monthlyBudgetTry):0,
    usdTry:cfg.usdTry,
    recent:rows.slice(-20).reverse()
  };
}

function json(res,status,obj){
  res.writeHead(status,{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"});
  res.end(JSON.stringify(obj));
}
async function readJson(req,max=18*1024*1024){
  return await new Promise((resolve,reject)=>{
    let size=0,chunks=[];
    req.on("data",c=>{size+=c.length;if(size>max){reject(new Error("İstek çok büyük"));req.destroy();return}chunks.push(c)});
    req.on("end",()=>{try{resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")||"{}"))}catch(e){reject(new Error("Geçersiz JSON"))}});
    req.on("error",reject);
  });
}
function extractOutputText(data){
  if(typeof data?.output_text==="string") return data.output_text;
  const out=[];
  for(const item of data?.output||[]){
    for(const c of item?.content||[]){
      if(typeof c?.text==="string") out.push(c.text);
    }
  }
  return out.join("\n");
}
function parseJsonText(txt){
  const raw=String(txt||"").trim().replace(/^```(?:json)?\s*/i,"").replace(/\s*```$/,"");
  try{return JSON.parse(raw)}catch{}
  const a=raw.indexOf("{"),b=raw.lastIndexOf("}");
  if(a>=0&&b>a) return JSON.parse(raw.slice(a,b+1));
  throw new Error("AI yanıtı JSON olarak ayrıştırılamadı");
}
async function openaiRequest({instructions,input,reasoning="low"}){
  const s=readSecrets();
  if(!s.openaiApiKey) throw new Error("OpenAI API anahtarı ayarlanmamış");
  const body={
    model:s.openaiModel||"gpt-5.6-luna",
    reasoning:{effort:reasoning},
    instructions,
    input,
    text:{verbosity:"low"}
  };
  const r=await fetch("https://api.openai.com/v1/responses",{
    method:"POST",
    headers:{"Authorization":`Bearer ${s.openaiApiKey}`,"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data?.error?.message||`OpenAI API HTTP ${r.status}`);
  return {data,text:extractOutputText(data),model:body.model};
}
function flattenCurriculum(curriculum,courses){
  const rows=[];
  for(const course of courses||[]){
    const units=curriculum?.[course]||{};
    for(const [unit,topics] of Object.entries(units)){
      for(const topic of topics||[]) rows.push({course,unit,topic});
    }
  }
  return rows;
}
function deterministicPlan(student,curriculum,resources=[]){
  const topics=flattenCurriculum(curriculum,student.courses);
  const start=new Date(student.registeredAt||new Date().toISOString().slice(0,10));
  const end=new Date(student.courseEndDate||start);
  const diff=Math.max(1,Math.floor((end-start)/(7*864e5))+1);
  const weeks=Array.from({length:diff},(_,i)=>({week:i+1,startDate:new Date(start.getTime()+i*7*864e5).toISOString().slice(0,10),items:[]}));
  topics.forEach((x,i)=>{
    const level=student.levels?.[x.course]||"Orta";
    const res=resources.find(r=>r.course===x.course&&r.topic===x.topic&&r.level===level)
      ||resources.find(r=>r.course===x.course&&r.topic===x.topic)||null;
    weeks[i%weeks.length].items.push({...x,type:"Yeni Konu",priority:"normal",resourceId:res?.id??null,estimatedMinutes:Math.min(90,Math.max(30,Math.round((student.dailyMinutes||120)/2)))});
  });
  return {mode:"deterministic",weeks,totalTopics:topics.length};
}
async function handleAiPlan(req,res){
  const body=await readJson(req,2*1024*1024);
  const {student,curriculum,results=[],resources=[]}=body;
  if(!student) return json(res,400,{ok:false,error:"Öğrenci verisi gerekli"});
  const fallback=deterministicPlan(student,curriculum||{},resources);
  if(!integrationStatus().openai.configured) return json(res,200,{ok:true,usedAi:false,plan:fallback,warning:"OpenAI API anahtarı ayarlı değil; deterministik plan üretildi."});
  const topics=flattenCurriculum(curriculum,student.courses);
  const prompt={
    student:{
      id:student.id,name:student.name,grade:student.grade,target:student.target,
      registeredAt:student.registeredAt,courseEndDate:student.courseEndDate,
      weeklyStudyDays:student.weeklyStudyDays,dailyMinutes:student.dailyMinutes,
      courses:student.courses,levels:student.levels
    },
    topics,
    recentResults:results.slice(-80),
    resources:resources.map(r=>({id:r.id,course:r.course,topic:r.topic,level:r.level,title:r.title})).slice(0,300)
  };
  const instructions=`Sen bir akademik koçluk planlama motorusun. Görevin öğrencinin kayıt tarihi ile kurs bitiş tarihi arasındaki haftalara tüm ünite/alt konu başlıklarını yetişecek şekilde dağıtmaktır.
Kurallar:
- Öğrencinin haftalık çalışma gününü ve günlük dakika sınırını aşma.
- Ön koşullu konuları mümkün olduğunca pedagojik sırada tut.
- Öğrencinin ders bazlı seviyesini dikkate al.
- Sonuçlarda başarı eşiğinin altında kalmış konular varsa erken haftalara "Tekrar" olarak ekle.
- Kaynak listesinde konu ve seviyeye uygun PDF varsa resourceId alanına koy; yoksa null.
- Aynı haftayı aşırı yükleme.
- Sadece geçerli JSON döndür.
Şema:
{"weeks":[{"week":1,"startDate":"YYYY-MM-DD","items":[{"course":"...","unit":"...","topic":"...","type":"Yeni Konu|Tekrar","priority":"high|normal","resourceId":number|null,"estimatedMinutes":number,"reason":"kısa gerekçe"}]}],"totalTopics":number,"notes":["..."]}`;
  const ai=await openaiRequest({instructions,input:JSON.stringify(prompt),reasoning:"medium"});
  const parsed=parseJsonText(ai.text);
  const cost=appendUsage("plan",ai.model,ai.data?.usage||{}, {studentId:student.id});
  return json(res,200,{ok:true,usedAi:true,plan:{mode:"ai",...parsed},usage:ai.data?.usage||null,cost});
}
async function handleHomework(req,res){
  const body=await readJson(req,18*1024*1024);
  const {fileData,mimeType="application/pdf",fileName="odev.pdf",assignment,answerKey=null}=body;
  if(!fileData) return json(res,400,{ok:false,error:"Ödev dosyası gerekli"});
  if(!integrationStatus().openai.configured) return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun. Yüklenen PDF/görselde öğrencinin işaretlerini, boş bıraktığı soruları ve mümkünse çözüm yollarını incele.
Eğer cevap anahtarı sağlandıysa onu kesin referans olarak kullan. Cevap anahtarı yoksa yalnızca güvenle değerlendirebildiklerini puanla ve confidence değerini düşür.
Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.
Sadece JSON döndür:
{"totalQuestions":number,"correct":number,"wrong":number,"blank":number,"scorePercent":number,"confidence":number,"items":[{"question":number,"status":"correct|wrong|blank|uncertain","studentAnswer":"string|null","correctAnswer":"string|null","errorType":"string|null","note":"string|null"}],"weaknesses":["..."],"recommendRepeat":boolean,"summary":"..."}`;
  const content=[
    {type:"input_text",text:JSON.stringify({assignment,answerKey})},
    {type:"input_file",filename:fileName,file_data:`data:${mimeType};base64,${fileData}`}
  ];
  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"medium"});
  const parsed=parseJsonText(ai.text);
  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  return json(res,200,{ok:true,analysis:parsed,usage:ai.data?.usage||null,cost});
}
async function handleYoutube(req,res){
  const body=await readJson(req,512*1024);
  const s=readSecrets();
  if(!s.youtubeApiKey) return json(res,400,{ok:false,error:"YouTube API anahtarı ayarlanmamış"});
  const query=String(body.query||"").trim();
  if(!query) return json(res,400,{ok:false,error:"Arama metni gerekli"});
  const max=Math.min(10,Math.max(1,Number(body.maxResults||5)));
  const u=new URL("https://www.googleapis.com/youtube/v3/search");
  u.searchParams.set("part","snippet");u.searchParams.set("type","video");u.searchParams.set("maxResults",String(max));
  u.searchParams.set("q",query);u.searchParams.set("key",s.youtubeApiKey);
  u.searchParams.set("safeSearch","strict");u.searchParams.set("relevanceLanguage","tr");
  const r=await fetch(u);const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data?.error?.message||`YouTube API HTTP ${r.status}`);
  const videos=(data.items||[]).map(v=>({
    videoId:v.id?.videoId,title:v.snippet?.title,channelTitle:v.snippet?.channelTitle,
    publishedAt:v.snippet?.publishedAt,thumbnail:v.snippet?.thumbnails?.medium?.url||v.snippet?.thumbnails?.default?.url,
    url:v.id?.videoId?`https://www.youtube.com/watch?v=${v.id.videoId}`:""
  }));
  json(res,200,{ok:true,videos});
}
function scheduleBootstrapMigration(){
  try{
    if(process.platform!=="win32") return;
    const ps1=path.join(runtime,"bootstrap_migrate_041.ps1");
    const batPath=path.join(root,"PROGRAMI_CALISTIR.bat");
    const bat=`@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title YILBAY OGRENCI TAKIP SISTEMI

echo ================================================================
echo       YILBAY OGRENCI TAKIP SISTEMI - KALICI BASLATICI
echo ================================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap\\orchestrator.ps1"
set EXITCODE=%ERRORLEVEL%
exit /b %EXITCODE%
`;
    const esc=s=>s.replace(/'/g,"''");
    const script=`$ErrorActionPreference='SilentlyContinue'
$Root='${esc(root)}'
$Bat='${esc(batPath)}'
$Content=@'
${bat.replace(/\r/g,"")}
'@
for($i=0;$i -lt 900;$i++){
  $running=Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'powershell.exe' -and $_.CommandLine -like '*bootstrap\\orchestrator.ps1*' -and $_.CommandLine -like ('*'+$Root+'*')
  }
  if(-not $running){break}
  Start-Sleep -Milliseconds 500
}
[System.IO.File]::WriteAllText($Bat,$Content,(New-Object System.Text.UTF8Encoding($false)))
Start-Sleep -Milliseconds 300
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'cmd.exe' -and $_.CommandLine -like '*PROGRAMI_CALISTIR.bat*' -and $_.CommandLine -like ('*'+$Root+'*')
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
`;
    fs.writeFileSync(ps1,script,"utf8");
    const child=cp.spawn("powershell.exe",["-NoProfile","-ExecutionPolicy","Bypass","-WindowStyle","Hidden","-File",ps1],{detached:true,stdio:"ignore",windowsHide:true});
    child.on("error",e=>console.error("BOOTSTRAP_MIGRATION_SPAWN_ERROR",e.message));child.unref();
  }catch(e){console.error("BOOTSTRAP_MIGRATION_ERROR",e.message)}
}
scheduleBootstrapMigration();

http.createServer(async(req,res)=>{
  try{
    const u=new URL(req.url,"http://127.0.0.1");
    if(u.pathname==="/health") return json(res,200,{ok:true,version:"0.6.8",integrations:integrationStatus()});
    if(u.pathname==="/api/integrations/status"&&req.method==="GET") return json(res,200,{ok:true,...integrationStatus()});
    if(u.pathname==="/api/ai/costs"&&req.method==="GET") return json(res,200,{ok:true,...costSummary()});
    if(u.pathname==="/api/integrations/settings"&&req.method==="POST"){
      const b=await readJson(req,128*1024),old=readStoredSecrets();
      writeSecrets({
        openaiApiKey:b.openaiApiKey==="__KEEP__"?old.openaiApiKey:b.openaiApiKey,
        youtubeApiKey:b.youtubeApiKey==="__KEEP__"?old.youtubeApiKey:b.youtubeApiKey,
        openaiModel:b.openaiModel||old.openaiModel||"gpt-5.6-luna",
        usdTry:b.usdTry??old.usdTry??48.12,
        monthlyBudgetTry:b.monthlyBudgetTry??old.monthlyBudgetTry??1000
      });
      return json(res,200,{ok:true,...integrationStatus()});
    }
    if(u.pathname==="/api/ai/plan"&&req.method==="POST") return await handleAiPlan(req,res);
    if(u.pathname==="/api/ai/analyze-homework"&&req.method==="POST") return await handleHomework(req,res);
    if(u.pathname==="/api/youtube/search"&&req.method==="POST") return await handleYoutube(req,res);
    let p=u.pathname==="/"?"/index.html":u.pathname;
    const f=path.normalize(path.join(pub,p));
    if(!f.startsWith(pub)){res.writeHead(403);return res.end("Forbidden")}
    fs.readFile(f,(e,d)=>{
      if(e){res.writeHead(404);return res.end("Not found")}
      const ext=path.extname(f).toLowerCase();
      const types={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".json":"application/json; charset=utf-8"};
      res.writeHead(200,{"Content-Type":types[ext]||"application/octet-stream"});res.end(d);
    });
  }catch(e){
    console.error("REQUEST_ERROR",e);
    if(!res.headersSent) json(res,500,{ok:false,error:e.message||"Sunucu hatası"});
  }
}).listen(port,"127.0.0.1",()=>console.log("READY 0.6.8"));


(function installNodeBootstrap(){
  if(process.platform!=="win32") return;
  try{
    const _fs=require("fs"),_path=require("path");
    const _root=_path.resolve(__dirname,"..");
    const _src=_path.join(__dirname,"bootstrap","orchestrator_node.js");
    const _dst=_path.join(_root,"bootstrap","orchestrator.js");
    if(_fs.existsSync(_src)){
      _fs.mkdirSync(_path.dirname(_dst),{recursive:true});
      _fs.copyFileSync(_src,_dst);
      const bat='@echo off\r\nsetlocal\r\nwhere node >nul 2>nul\r\nif %ERRORLEVEL%==0 (\r\n  node "%~dp0bootstrap\\orchestrator.js"\r\n  exit /b %ERRORLEVEL%\r\n)\r\necho Node.js bulunamadi. Eski baslatma yontemine geciliyor.\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap\\orchestrator.ps1"\r\nexit /b %ERRORLEVEL%\r\n';
      _fs.writeFileSync(_path.join(_root,"PROGRAMI_CALISTIR.bat"),bat,"utf8");
      _fs.writeFileSync(_path.join(_root,"BOOTSTRAP_VERSION"),'2.0.0-node\n','utf8');
      console.log('NODE_BOOTSTRAP_MIGRATION_READY');
    }
  }catch(e){ console.error('NODE_BOOTSTRAP_MIGRATION_ERROR',e.message); }
})();
