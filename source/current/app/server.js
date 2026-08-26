/* CELL:00-runtime | layer:backend | generated-from:v0.7.2 */
const http=require("http"),fs=require("fs"),path=require("path"),cp=require("child_process");


const port=Number(process.env.PORT||43127), pub=path.join(__dirname,"public");


const root=path.resolve(__dirname,"..");


const runtime=path.join(root,"runtime");


const secretFile=path.join(runtime,"api_secrets.json");


const usageFile=path.join(runtime,"ai_usage.jsonl");


fs.mkdirSync(runtime,{recursive:true});



/* CELL:10-secrets-integrations | layer:backend | generated-from:v0.7.2 */

/* CELL:10-secrets-integrations | layer:backend | generated-from:v0.7.2 */
const OPENAI_CREDENTIAL_TARGET="YILBAY-OPENAI-API-HOME";


const OPENAI_CREDENTIAL_USERNAME="YILBAY-DEVELOPMENT-HOME";


function readStoredSecrets(){
  try{return JSON.parse(fs.readFileSync(secretFile,"utf8"))}catch{return {}}
}


function readWindowsCredential(){
  return {value:null,diagnostic:{method:"disabled-environment-mode",found:false,userMatch:false,targetMatched:false}};
}


function readSecrets(){
  const stored=readStoredSecrets();
  const envKey=String(process.env.OPENAI_API_KEY||"").trim();
  const manual=String(stored.openaiApiKey||"").trim();
  let openaiApiKey="",openaiApiSource="none";
  if(envKey){ openaiApiKey=envKey; openaiApiSource="environment"; }
  else if(manual){ openaiApiKey=manual; openaiApiSource="manual"; }
  return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:{method:"disabled-environment-mode",found:false,userMatch:false,targetMatched:false}};
}


function writeSecrets(next){
  const clean={
    openaiApiKey:String(next.openaiApiKey||"").trim(),
    youtubeApiKey:String(next.youtubeApiKey||"").trim(),
    driveClientId:String(next.driveClientId||"").trim(),
    driveClientSecret:String(next.driveClientSecret||"").trim(),
    driveFolderId:String(next.driveFolderId||"").trim(),
    driveRefreshToken:String(next.driveRefreshToken||"").trim(),
    driveAccessToken:String(next.driveAccessToken||"").trim(),
    driveAccessTokenExpiresAt:Number(next.driveAccessTokenExpiresAt||0)||0,
    driveOauthState:String(next.driveOauthState||"").trim(),
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
    drive:{configured:!!(s.driveClientId&&s.driveClientSecret),connected:!!s.driveRefreshToken,folderConfigured:!!s.driveFolderId,mode:"oauth-readonly"},
    cost:{usdTry:Number(s.usdTry||48.12)||48.12,monthlyBudgetTry:Number(s.monthlyBudgetTry||1000)||1000}
  };
}

/* CELL:20-cost-accounting | layer:backend | generated-from:v0.7.2 */

/* CELL:20-cost-accounting | layer:backend | generated-from:v0.7.2 */
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

/* CELL:30-http-openai-core | layer:backend | generated-from:v0.7.2 */

/* CELL:30-http-openai-core | layer:backend | generated-from:v0.7.2 */
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


async function handleAiPing(req,res){
  const status=integrationStatus();
  if(!status.openai.configured) return json(res,400,{ok:false,error:"OpenAI API anahtarı bağlı değil"});
  const started=Date.now();
  const ai=await openaiRequest({instructions:"Yalnızca OK yaz.",input:"Bağlantı testi",reasoning:"low"});
  const cost=appendUsage("connection_test",ai.model,ai.data?.usage||{},{});
  return json(res,200,{ok:true,connected:true,model:ai.model,latencyMs:Date.now()-started,response:String(ai.text||"").trim().slice(0,80),usage:ai.data?.usage||null,cost});
}

/* CELL:40-academic-planner | layer:backend | generated-from:v0.7.2 */

/* CELL:40-academic-planner | layer:backend | generated-from:v0.7.2 */
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

/* CELL:50-homework-vision | layer:backend | generated-from:v0.7.2 */

/* CELL:50-homework-vision | layer:backend | generated-from:v0.7.2 */
function normalizeHomeworkAnalysis(x={}){
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,Number.isFinite(Number(n))?Number(n):a));
  const correct=Math.max(0,Math.round(Number(x.correct)||0));
  const wrong=Math.max(0,Math.round(Number(x.wrong)||0));
  const blank=Math.max(0,Math.round(Number(x.blank)||0));
  const total=Math.max(0,Math.round(Number(x.totalQuestions)||correct+wrong+blank));
  let score=Number(x.scorePercent);
  if(!Number.isFinite(score) && correct+wrong+blank>0) score=100*correct/(correct+wrong+blank);
  score=clamp(score,0,100);
  const confidence=clamp(x.confidence,0,1);
  const modelReview=!!x.needsTeacherReview;
  const reviewRequired=modelReview || confidence<0.65 || total===0;
  return {
    ...x,
    correct,wrong,blank,totalQuestions:total,
    scorePercent:Math.round(score*10)/10,
    confidence:Math.round(confidence*1000)/1000,
    needsTeacherReview:reviewRequired,
    autoFinalize:!reviewRequired,
    weaknesses:Array.isArray(x.weaknesses)?x.weaknesses.slice(0,20):[],
    errorTypes:Array.isArray(x.errorTypes)?x.errorTypes.slice(0,30):[],
    notes:Array.isArray(x.notes)?x.notes.slice(0,20):[]
  };
}


async function driveDownloadAnalysisFile(fileId){if(!fileId)return null;const token=await driveRefreshAccessToken();const u='https://www.googleapis.com/drive/v3/files/'+encodeURIComponent(fileId)+'?alt=media';const r=await fetch(u,{headers:{Authorization:'Bearer '+token}});if(!r.ok){let j={};try{j=await r.json()}catch{}throw new Error(j.error?.message||('Drive dosyası indirilemedi HTTP '+r.status))}const b=Buffer.from(await r.arrayBuffer());if(b.length>14*1024*1024)throw new Error('Drive analiz dosyası 14 MB sınırını aşıyor');return {base64:b.toString('base64'),mimeType:r.headers.get('content-type')||'application/pdf',size:b.length}}
function validateHomeworkQuestionCount(analysis,expected){const n=Math.max(0,Math.round(Number(expected)||0));if(!n)return analysis;if(Number(analysis.totalQuestions)!==n)return {...analysis,needsTeacherReview:true,autoFinalize:false,questionCountMismatch:true,expectedQuestionCount:n};return {...analysis,expectedQuestionCount:n,questionCountMismatch:false}}
function homeworkAnswerKeySearchInstruction(){return `CEVAP ANAHTARI ARAMA PROTOKOLÜ:
Önce manuel veya ayrı cevap anahtarı verilmişse onu kesin referans kabul et. Ayrı anahtar yoksa KAYNAK PDF'nin tamamında cevap anahtarı ara. Cevap anahtarı testin bulunduğu aynı sayfanın üstünde veya altında, bir sonraki sayfanın üstünde veya altında, PDF'nin son sayfalarında ya da son sayfalarda test isimleriyle toplu tabloda olabilir. Toplu cevap anahtarında assignment.title, resourceContext.title, course ve topic bilgilerini kullanarak doğru test bloğunu eşleştir. Öğrencinin kendi işaretlerini asla cevap anahtarı sayma. Birden fazla blok aynı derecede olasıysa answerKeySource=\"ambiguous\" yap. Hiç güvenilir anahtar yoksa answerKeySource=\"none\" yap. Gömülü anahtar bulunduğunda source yalnız embedded_same_page, embedded_adjacent_page veya embedded_end_pages olabilir. answerKeyConfidence cevap anahtarının gerçekten ilgili teste ait olma güvenidir.`}
function validateHomeworkAnswerKeyEvidence(analysis,manualAnswerKey,resourceContext){const manual=String(manualAnswerKey||'').trim(),external=String(resourceContext?.answerKeyDriveFileId||'').trim();if(manual)return {...analysis,answerKeyFound:true,answerKeySource:'manual',answerKeyConfidence:1,answerKeyEvidence:analysis.answerKeyEvidence||'Öğretmen tarafından manuel cevap anahtarı sağlandı'};if(external)return {...analysis,answerKeyFound:true,answerKeySource:'external_drive',answerKeyConfidence:1,answerKeyEvidence:analysis.answerKeyEvidence||'Ayrı Drive cevap anahtarı sağlandı'};const allowed=['embedded_same_page','embedded_adjacent_page','embedded_end_pages'],source=String(analysis.answerKeySource||'none'),confidence=Math.max(0,Math.min(1,Number(analysis.answerKeyConfidence)||0)),found=analysis.answerKeyFound===true&&allowed.includes(source),review=!found||confidence<0.75;return {...analysis,answerKeyFound:found,answerKeySource:found?source:(source==='ambiguous'?'ambiguous':'none'),answerKeyConfidence:Math.round(confidence*1000)/1000,answerKeyEvidence:String(analysis.answerKeyEvidence||'').slice(0,500),needsTeacherReview:!!analysis.needsTeacherReview||review,autoFinalize:!!analysis.autoFinalize&&!review}}
function estimatePdfPageCount(base64,mimeType='application/pdf'){if(!String(mimeType||'').toLowerCase().includes('pdf'))return 1;try{const text=Buffer.from(String(base64||''),'base64').toString('latin1');const direct=(text.match(/\/Type\s*\/Page\b/g)||[]).length;const counts=[...text.matchAll(/\/Count\s+(\d+)/g)].map(x=>Number(x[1])||0).filter(n=>n>0&&n<5000);return Math.max(direct,counts.length?Math.max(...counts):0)}catch{return 0}}
function validateHomeworkPageCoverage(x={},expectedStudentPages=0,expectedSourcePages=0){const normalize=a=>Array.isArray(a)?[...new Set(a.map(Number).filter(n=>Number.isInteger(n)&&n>0))].sort((a,b)=>a-b):[];const student=normalize(x.analyzedStudentPages),source=normalize(x.analyzedSourcePages);const missing=(expected,list)=>expected>0?Array.from({length:expected},(_,i)=>i+1).filter(n=>!list.includes(n)):[];const missingStudentPages=missing(expectedStudentPages,student),missingSourcePages=missing(expectedSourcePages,source);const studentVerified=expectedStudentPages>0&&missingStudentPages.length===0;const sourceVerified=expectedSourcePages===0||missingSourcePages.length===0;const pdfCoverageVerified=studentVerified&&sourceVerified;const reviewRequired=!!x.needsTeacherReview||!pdfCoverageVerified;return {...x,expectedStudentPages,expectedSourcePages,analyzedStudentPages:student,analyzedSourcePages:source,analyzedPageCount:student.length,missingStudentPages,missingSourcePages,pdfCoverageVerified,needsTeacherReview:reviewRequired,autoFinalize:!reviewRequired}}
function writeHomeworkDiagnostic(analysis={},cost=null,assignment=null){const safe={timestamp:new Date().toISOString(),assignmentId:assignment?.id??null,expectedStudentPages:Number(analysis.expectedStudentPages)||0,analyzedStudentPages:Array.isArray(analysis.analyzedStudentPages)?analysis.analyzedStudentPages.slice(0,500):[],missingStudentPages:Array.isArray(analysis.missingStudentPages)?analysis.missingStudentPages.slice(0,500):[],expectedSourcePages:Number(analysis.expectedSourcePages)||0,sourcePageCountStatus:Number(analysis.expectedSourcePages)>0?'known':'unknown',assignmentMatchFound:!!analysis.assignmentMatchFound,assignmentMatchConfidence:Number(analysis.assignmentMatchConfidence)||0,matchedQuestionCount:Number(analysis.matchedQuestionCount)||0,matchedQuestionNumbers:Array.isArray(analysis.matchedQuestionNumbers)?analysis.matchedQuestionNumbers.slice(0,500):[],assignmentScopeCountVerified:!!analysis.assignmentScopeCountVerified,assignmentScopeDuplicateCount:Number(analysis.assignmentScopeDuplicateCount)||0,analyzedSourcePages:Array.isArray(analysis.analyzedSourcePages)?analysis.analyzedSourcePages.slice(0,500):[],missingSourcePages:Array.isArray(analysis.missingSourcePages)?analysis.missingSourcePages.slice(0,500):[],pdfCoverageVerified:!!analysis.pdfCoverageVerified,answerKeyFound:!!analysis.answerKeyFound,answerKeySource:String(analysis.answerKeySource||'none'),answerKeyConfidence:Number(analysis.answerKeyConfidence)||0,confidence:Number(analysis.confidence)||0,needsTeacherReview:!!analysis.needsTeacherReview,autoFinalize:!!analysis.autoFinalize,totalQuestions:Number(analysis.totalQuestions)||0,correct:Number(analysis.correct)||0,wrong:Number(analysis.wrong)||0,blank:Number(analysis.blank)||0,scorePercent:Number(analysis.scorePercent)||0,classifiedQuestions:Number(analysis.classifiedQuestions)||0,questionAccountingVerified:!!analysis.questionAccountingVerified,expectedQuestionCount:Number(analysis.expectedQuestionCount)||0,questionCountMismatch:!!analysis.questionCountMismatch,reviewReasons:Array.isArray(analysis.reviewReasons)?analysis.reviewReasons.slice(0,20):[],costTry:Number(cost?.try)||0,secretsCollected:false,contentCollected:false};fs.mkdirSync(runtime,{recursive:true});fs.writeFileSync(path.join(runtime,'last_homework_analysis.json'),JSON.stringify(safe,null,2),'utf8');return safe}
function validateHomeworkQuestionAccounting(x={}){const total=Math.max(0,Math.round(Number(x.totalQuestions)||0)),correct=Math.max(0,Math.round(Number(x.correct)||0)),wrong=Math.max(0,Math.round(Number(x.wrong)||0)),blank=Math.max(0,Math.round(Number(x.blank)||0)),classifiedQuestions=correct+wrong+blank,questionAccountingVerified=total>0&&classifiedQuestions===total;const reviewRequired=!!x.needsTeacherReview||!questionAccountingVerified;return {...x,totalQuestions:total,correct,wrong,blank,classifiedQuestions,questionAccountingVerified,needsTeacherReview:reviewRequired,autoFinalize:!!x.autoFinalize&&!reviewRequired}}
function deriveHomeworkReviewReasons(x={}){const reasons=[];if(Number(x.confidence||0)<0.65)reasons.push('low_confidence');if(Number(x.totalQuestions||0)<=0)reasons.push('no_questions');if(x.questionCountMismatch)reasons.push('question_count_mismatch');if(x.questionAccountingVerified===false)reasons.push('question_accounting_mismatch');if(x.pdfCoverageVerified===false)reasons.push('page_coverage_incomplete');if(x.answerKeyFound!==true)reasons.push(x.answerKeySource==='ambiguous'?'answer_key_ambiguous':'answer_key_missing');else if(Number(x.answerKeyConfidence||0)<0.75)reasons.push('answer_key_low_confidence');if(x.needsTeacherReview&&reasons.length===0)reasons.push('model_requested_review');return {...x,reviewReasons:[...new Set(reasons)].slice(0,20)}}
async function resolveStudentHomeworkFile(body={}){const source=String(body.studentFileSource||'local');if(source==='local'){if(!body.fileData)throw new Error('Ödev dosyası gerekli');return {source:'local',base64:body.fileData,mimeType:body.mimeType||'application/pdf',fileName:body.fileName||'odev.pdf',driveUsed:false}}if(source==='drive'){if(!body.studentDriveFileId)throw new Error('Drive ödev dosyası kimliği gerekli');const f=await driveDownloadAnalysisFile(body.studentDriveFileId);return {source:'drive',base64:f.base64,mimeType:f.mimeType||'application/pdf',fileName:body.fileName||'drive_odev.pdf',driveUsed:true}}throw new Error('Geçersiz ödev dosyası kaynağı')}
function homeworkReasoningInstruction(){return 'EL YAZISI ÇÖZÜM ANALİZİ PROTOKOLÜ: Her soruda yalnız son cevabı değil öğrencinin görülebilen el yazısı çözümünü de incele. approach alanında yöntemi özetle. stepsSummary görülen temel adımları sırayla vermeli. firstErrorStep ilk hatalı veya eksik adımı belirtir. errorCategory yalnız conceptual|arithmetic|attention|method|incomplete|none|uncertain değerlerinden biri olsun. conceptualIssue, arithmeticIssue ve attentionIssue alanlarını gerektiğinde doldur. methodQuality efficient|acceptable|inefficient|incorrect|uncertain olsun. Doğru sonuca hatalı veya tesadüfi yöntemle ulaşıldıysa note içinde açıkça belirt. unnecessarySteps ve missingSteps dizilerini üret. betterApproach daha uygun yöntemi kısa ve pedagojik biçimde açıklar. learningObjective tekrar edilmesi gereken kazanımı belirtir. solutionConfidence 0-1 arasıdır. El yazısı okunamıyorsa tahmin etme, uncertain yap. Üst düzey reasoningProfile içinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary üret.'}
function homeworkAssignmentScopeInstruction(){return `ATAMA SORU KAPSAMI PROTOKOLÜ:
Önce bu atamaya ait soru kümesini belirle; sonra yalnız bu kümeyi puanla ve çözüm yaklaşımını raporla. Kimlik olarak yalnız PDF üzerinde basılı/orijinal soru numaralarını kullan. Sayfada görünme sırası, kırpma sırası veya modelin kendi sayacı soru kimliği değildir. assignment.title, course, topic, resourceContext.title, unit, questionCount ve varsa test adı/başlığı ile eşleştir. PDF birden fazla test içeriyorsa yalnız atamaya ait testi seç. matchedQuestionNumbers benzersiz ve artan basılı soru numaraları olmalı. Beklenen questionCount varsa tam o kadar soru güvenle eşleşmedikçe assignmentMatchFound=false veya assignmentMatchConfidence düşük ver ve needsTeacherReview=true yap. Eşleşmeyen diğer testleri doğru/yanlış/boş toplamlarına katma. assignmentMatchEvidence hangi başlık/test/sayfa işaretleriyle eşleştiğini kısa açıklar.`}
function validateHomeworkAssignmentScope(analysis={},expected=0){const nums=Array.isArray(analysis.matchedQuestionNumbers)?analysis.matchedQuestionNumbers.map(Number).filter(n=>Number.isInteger(n)&&n>0):[];const unique=[...new Set(nums)].sort((a,b)=>a-b);const n=Math.max(0,Math.round(Number(expected)||0));const duplicateCount=Math.max(0,nums.length-unique.length);const confidence=Math.max(0,Math.min(1,Number(analysis.assignmentMatchConfidence)||0));const declared=analysis.assignmentMatchFound===true;const countOk=!n||unique.length===n;const found=declared&&duplicateCount===0&&countOk&&confidence>=0.75;return {...analysis,matchedQuestionNumbers:unique,matchedQuestionCount:unique.length,assignmentMatchConfidence:Math.round(confidence*1000)/1000,assignmentMatchFound:found,assignmentScopeDuplicateCount:duplicateCount,assignmentScopeCountVerified:countOk,assignmentMatchEvidence:String(analysis.assignmentMatchEvidence||'').slice(0,500),needsTeacherReview:!!analysis.needsTeacherReview||!found,autoFinalize:!!analysis.autoFinalize&&found}}
async function handleHomework(req,res){
  const body=await readJson(req,18*1024*1024);
  const {assignment,answerKey=null,resourceContext=null,studentFileSource="local"}=body;
  let studentFile;try{studentFile=await resolveStudentHomeworkFile(body)}catch(e){return json(res,400,{ok:false,error:e.message})}
  const {base64:fileData,mimeType,fileName}=studentFile;
  if(!integrationStatus().openai.configured) return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const answerKeySearch=homeworkAnswerKeySearchInstruction();
  const reasoningInstruction=homeworkReasoningInstruction();
  const assignmentScopeInstruction=homeworkAssignmentScopeInstruction();
  const expectedStudentPages=estimatePdfPageCount(fileData,mimeType);
  let expectedSourcePages=0;
  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun. Yüklenen PDF/görselin SADECE İLK SAYFASINI DEĞİL TÜM SAYFALARINI 1. sayfadan son sayfaya kadar sırayla incele. Hiçbir sayfayı atlama. Öğrencinin işaretlerini, boş bıraktığı soruları ve mümkünse çözüm yollarını tüm belge boyunca incele.
${answerKeySearch}
${reasoningInstruction}
${assignmentScopeInstruction}
Cevap anahtarı kanıtı olmadan doğru/yanlış durumunu kesinmiş gibi uydurma.
Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.
Kesin göremediğin işaret veya çözüm için tahmin yürütme. Soruların/işaretlerin yeterli kısmı okunamıyorsa needsTeacherReview=true yap.
confidence 0 ile 1 arasında olmalı. confidence 0.65 altındaysa sonuç öğretmen onayı gerektirmelidir. Her öğrenci PDF sayfasını gerçekten inceledikten sonra analyzedStudentPages alanına sayfa numaralarını tek tek yaz. Kaynak PDF verildiyse cevap anahtarı araması dahil tüm gerekli kaynak sayfalarını incele ve analyzedSourcePages alanına yaz.
Sadece JSON döndür:
{"assignmentMatchFound":boolean,"assignmentMatchConfidence":number,"assignmentMatchEvidence":"string","matchedTestName":"string|null","matchedQuestionNumbers":[number],"totalQuestions":number,"correct":number,"wrong":number,"blank":number,"scorePercent":number,"confidence":number,"items":[{"question":number,"status":"correct|wrong|blank|uncertain","studentAnswer":"string|null","correctAnswer":"string|null","approach":"string|null","stepsSummary":["string"],"firstErrorStep":"string|null","errorCategory":"conceptual|arithmetic|attention|method|incomplete|none|uncertain","conceptualIssue":"string|null","arithmeticIssue":"string|null","attentionIssue":"string|null","methodQuality":"efficient|acceptable|inefficient|incorrect|uncertain","unnecessarySteps":["string"],"missingSteps":["string"],"betterApproach":"string|null","learningObjective":"string|null","solutionConfidence":number,"errorType":"string|null","note":"string|null"}],"reasoningProfile":{"strengths":["string"],"recurringErrors":["string"],"conceptualGaps":["string"],"proceduralGaps":["string"],"attentionPatterns":["string"],"recommendedActions":["string"],"summary":"string"},"weaknesses":["..."],"recommendRepeat":boolean,"summary":"...","answerKeyFound":boolean,"answerKeySource":"manual|external_drive|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none","answerKeyConfidence":number,"answerKeyEvidence":"kısa konum/eşleşme açıklaması","answerKeyTestName":"string|null","studentDocumentPageCount":number,"analyzedStudentPages":[number],"sourceDocumentPageCount":number,"analyzedSourcePages":[number]}`;
  const content=[{type:"input_text",text:JSON.stringify({assignment,answerKey,resourceContext})}];
  if(studentFileSource==="drive"&&resourceContext?.driveFileId){const src=await driveDownloadAnalysisFile(resourceContext.driveFileId);expectedSourcePages=estimatePdfPageCount(src.base64,src.mimeType);content.push({type:"input_text",text:`KAYNAK PDF - tüm gerekli sayfaları incele. Beklenen sayfa sayısı: ${expectedSourcePages||"bilinmiyor"}`},{type:"input_file",filename:"kaynak.pdf",file_data:`data:${src.mimeType};base64,${src.base64}`})}
  if(studentFileSource==="drive"&&resourceContext?.answerKeyDriveFileId){const key=await driveDownloadAnalysisFile(resourceContext.answerKeyDriveFileId);content.push({type:"input_text",text:"CEVAP ANAHTARI - kesin referans olarak kullan"},{type:"input_file",filename:"cevap_anahtari.pdf",file_data:`data:${key.mimeType};base64,${key.base64}`})}
  content.push({type:"input_text",text:`ÖĞRENCİ ÇÖZÜM DOSYASI - TÜM SAYFALARI tara. Beklenen sayfa sayısı: ${expectedStudentPages||"bilinmiyor"}. İlk sayfada durma.`},{type:"input_file",filename:fileName,file_data:`data:${mimeType};base64,${fileData}`});
  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"medium"});
  const parsed=deriveHomeworkReviewReasons(validateHomeworkQuestionAccounting(validateHomeworkAssignmentScope(validateHomeworkPageCoverage(validateHomeworkAnswerKeyEvidence(validateHomeworkQuestionCount(normalizeHomeworkAnalysis(parseJsonText(ai.text)),resourceContext?.questionCount),answerKey,resourceContext),expectedStudentPages,expectedSourcePages),resourceContext?.questionCount)));
  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  parsed.studentFileSource=studentFileSource;parsed.studentFileDriveUsed=!!studentFile.driveUsed;
  writeHomeworkDiagnostic(parsed,cost,assignment);
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});
}

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */
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

/* CELL:70-routes | layer:backend | generated-from:v0.7.2 */

/* CELL:70-routes | layer:backend | generated-from:v0.7.2 */

function driveRedirectUri(){return `http://127.0.0.1:${port}/api/drive/oauth/callback`}
function driveTokenSavePatch(patch){const old=readStoredSecrets();return writeSecrets({...old,...patch})}
async function driveRefreshAccessToken(){const st=readStoredSecrets();if(st.driveAccessToken&&Number(st.driveAccessTokenExpiresAt||0)>Date.now()+60000)return st.driveAccessToken;if(!st.driveRefreshToken)throw new Error("Google Drive yetkilendirmesi yok");const body=new URLSearchParams({client_id:st.driveClientId,client_secret:st.driveClientSecret,refresh_token:st.driveRefreshToken,grant_type:"refresh_token"});const r=await fetch("https://oauth2.googleapis.com/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error_description||j.error||`Google token HTTP ${r.status}`);driveTokenSavePatch({driveAccessToken:j.access_token,driveAccessTokenExpiresAt:Date.now()+Math.max(60,Number(j.expires_in||3600))*1000});return j.access_token}
function normalizeCourseName(value){const raw=String(value||'').trim().replace(/\s+/g,' ');const key=raw.toLocaleLowerCase('tr-TR').replace(/[\s_.-]+/g,'');const aliases={lgsmatematik:'LGS Matematik',tytmatematik:'TYT Matematik',aytmatematik:'AYT Matematik',lgsgeometri:'LGS Geometri',tytgeometri:'TYT Geometri',aytgeometri:'AYT Geometri',turkce:'Türkçe',paragraf:'Paragraf',problemler:'Problemler'};return aliases[key]||raw.replace(/\b(lgs|tyt|ayt)\b/gi,x=>x.toUpperCase())}
function parseDriveResourceFilename(name){const base=String(name||'').replace(/\.pdf$/i,'');const parts=base.split('__').map(x=>x.trim()).filter(Boolean);if(parts.length>=6){const [course,unit,subtopic,level,count,...titleParts]=parts;return {course,unit,subtopic,topic:subtopic,level,questionCount:Math.max(0,Number(count)||0),title:titleParts.join('__')}}if(parts.length>=4){const [course,topic,level,...titleParts]=parts;return {course,unit:'',subtopic:topic,topic,level,questionCount:0,title:titleParts.join('__')}}return {course:'',unit:'',subtopic:'',topic:'',level:'',questionCount:0,title:base}}
function driveMetadataFromFile(file){const ap=file.appProperties||{},parsed=parseDriveResourceFilename(file.name);let course=String(ap.yilbayCourse||parsed.course||'').trim(),unit=String(ap.yilbayUnit||parsed.unit||'').trim(),subtopic=String(ap.yilbaySubtopic||parsed.subtopic||'').trim(),topic=String(ap.yilbayTopic||parsed.topic||subtopic||'').trim(),level=String(ap.yilbayLevel||parsed.level||'').trim(),title=String(ap.yilbayTitle||parsed.title||'').trim(),questionCount=Math.max(0,Number(ap.yilbayQuestionCount||parsed.questionCount)||0),answerKeyDriveFileId=String(ap.yilbayAnswerKeyDriveFileId||'').trim();course=normalizeCourseName(course);return {course,unit,subtopic:subtopic||topic,topic:topic||subtopic,level,title:title||String(file.name||'').replace(/\.pdf$/i,''),questionCount,answerKeyDriveFileId,matched:!!(course&&(topic||subtopic)&&level)}}
function isDriveAnswerKeyFile(file){return /__(CEVAP|CEVAP[_ -]?ANAHTARI|ANSWER[_ -]?KEY)\.pdf$/i.test(String(file?.name||''))}
function drivePairKey(name){return String(name||'').replace(/\.pdf$/i,'').replace(/__(CEVAP|CEVAP[_ -]?ANAHTARI|ANSWER[_ -]?KEY)$/i,'').trim().toLocaleLowerCase('tr-TR').replace(/\s+/g,' ')}
function pairDriveAnswerKeys(files){const keys=new Map(),sources=[];for(const f of files||[]){const k=drivePairKey(f.name);if(isDriveAnswerKeyFile(f)){const a=keys.get(k)||[];a.push(f);keys.set(k,a)}else sources.push(f)}let paired=0,ambiguous=0;const items=sources.map(f=>{const md=driveMetadataFromFile(f),candidates=keys.get(drivePairKey(f.name))||[];let answerKeyDriveFileId=md.answerKeyDriveFileId||'',answerKeyAutoMatched=false,answerKeyAmbiguous=false;if(!answerKeyDriveFileId&&candidates.length===1){answerKeyDriveFileId=candidates[0].id;answerKeyAutoMatched=true;paired++}else if(!answerKeyDriveFileId&&candidates.length>1){answerKeyAmbiguous=true;ambiguous++}return {...f,...md,answerKeyDriveFileId,answerKeyAutoMatched,answerKeyAmbiguous}});return {items,answerKeyCount:[...keys.values()].reduce((n,a)=>n+a.length,0),pairedAnswerKeyCount:paired,ambiguousAnswerKeyCount:ambiguous,unpairedAnswerKeyCount:[...keys.values()].reduce((n,a)=>n+a.length,0)-paired}}
async function driveListPdfIndex(){const st=readStoredSecrets();if(!st.driveFolderId)throw new Error("Google Drive kaynak klasörü ayarlanmamış");const token=await driveRefreshAccessToken();let pageToken="",files=[];do{const q=`'${String(st.driveFolderId).replace(/'/g,"\\'")}' in parents and mimeType='application/pdf' and trashed=false`;const u=new URL("https://www.googleapis.com/drive/v3/files");u.searchParams.set("q",q);u.searchParams.set("pageSize","1000");u.searchParams.set("fields","nextPageToken,files(id,name,mimeType,modifiedTime,size,webViewLink,appProperties)");if(pageToken)u.searchParams.set("pageToken",pageToken);const r=await fetch(u,{headers:{Authorization:`Bearer ${token}`}});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error?.message||`Drive API HTTP ${r.status}`);files.push(...(j.files||[]));pageToken=j.nextPageToken||""}while(pageToken);return pairDriveAnswerKeys(files)}
async function handleDriveOauthStart(req,res){const st=readStoredSecrets();if(!(st.driveClientId&&st.driveClientSecret))return json(res,400,{ok:false,error:"Google Drive OAuth Client ID/Secret ayarlanmamış"});const state=require("crypto").randomBytes(20).toString("hex");driveTokenSavePatch({driveOauthState:state});const u=new URL("https://accounts.google.com/o/oauth2/v2/auth");u.searchParams.set("client_id",st.driveClientId);u.searchParams.set("redirect_uri",driveRedirectUri());u.searchParams.set("response_type","code");u.searchParams.set("scope","https://www.googleapis.com/auth/drive.readonly");u.searchParams.set("access_type","offline");u.searchParams.set("prompt","consent");u.searchParams.set("state",state);return json(res,200,{ok:true,authorizationUrl:u.toString(),redirectUri:driveRedirectUri()})}
async function handleDriveOauthCallback(u,res){const st=readStoredSecrets();if(!u.searchParams.get("code")||u.searchParams.get("state")!==st.driveOauthState){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"});return res.end("<h2>Google Drive yetkilendirmesi doğrulanamadı.</h2>")}const body=new URLSearchParams({code:u.searchParams.get("code"),client_id:st.driveClientId,client_secret:st.driveClientSecret,redirect_uri:driveRedirectUri(),grant_type:"authorization_code"});const r=await fetch("https://oauth2.googleapis.com/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body});const j=await r.json().catch(()=>({}));if(!r.ok){res.writeHead(400,{"Content-Type":"text/html; charset=utf-8"});return res.end("<h2>Google Drive bağlantısı tamamlanamadı.</h2>")}driveTokenSavePatch({driveRefreshToken:j.refresh_token||st.driveRefreshToken||"",driveAccessToken:j.access_token||"",driveAccessTokenExpiresAt:Date.now()+Math.max(60,Number(j.expires_in||3600))*1000,driveOauthState:""});res.writeHead(200,{"Content-Type":"text/html; charset=utf-8"});res.end("<h2>Google Drive bağlandı.</h2><p>Bu pencereyi kapatıp YILBAY uygulamasına dönebilirsiniz.</p>")}
async function handleDriveIndex(req,res){const result=await driveListPdfIndex(),items=result.items||[];return json(res,200,{ok:true,items,matchedCount:items.filter(x=>x.matched).length,unmatchedCount:items.filter(x=>!x.matched).length,answerKeyCount:result.answerKeyCount||0,pairedAnswerKeyCount:result.pairedAnswerKeyCount||0,ambiguousAnswerKeyCount:result.ambiguousAnswerKeyCount||0,unpairedAnswerKeyCount:result.unpairedAnswerKeyCount||0})}

function installLaunchPreferences(){if(process.platform!=='win32')return {skipped:true};const src=path.join(__dirname,'bootstrap','orchestrator_node.js'),dstDir=path.join(root,'bootstrap'),dst=path.join(dstDir,'orchestrator_node.js');fs.mkdirSync(dstDir,{recursive:true});if(fs.existsSync(src))fs.copyFileSync(src,dst);const bat='@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\nstart "YILBAY" /MAX powershell.exe -NoLogo -NoProfile -Command "node \'%~dp0bootstrap/orchestrator_node.js\'"\r\nexit /b 0\r\n';fs.writeFileSync(path.join(root,'PROGRAMI_CALISTIR.bat'),bat,'utf8');return {installed:true}}
installLaunchPreferences()
http.createServer(async(req,res)=>{
  try{
    const u=new URL(req.url,"http://127.0.0.1");
    if(u.pathname==="/health") return json(res,200,{ok:true,version:"0.10.4",integrations:integrationStatus()});
    if(u.pathname==="/api/integrations/status"&&req.method==="GET") return json(res,200,{ok:true,...integrationStatus()});
    if(u.pathname==="/api/ai/costs"&&req.method==="GET") return json(res,200,{ok:true,...costSummary()});
    if(u.pathname==="/api/drive/status"&&req.method==="GET"){const d=integrationStatus().drive;return json(res,200,{ok:true,...d})}
    if(u.pathname==="/api/drive/oauth/start"&&req.method==="POST") return await handleDriveOauthStart(req,res);
    if(u.pathname==="/api/drive/oauth/callback"&&req.method==="GET") return await handleDriveOauthCallback(u,res);
    if(u.pathname==="/api/drive/index"&&req.method==="POST") return await handleDriveIndex(req,res);
    if(u.pathname==="/api/drive/disconnect"&&req.method==="POST"){const old=readStoredSecrets();writeSecrets({...old,driveRefreshToken:"",driveAccessToken:"",driveAccessTokenExpiresAt:0,driveOauthState:""});return json(res,200,{ok:true})}
    if(u.pathname==="/api/integrations/settings"&&req.method==="POST"){
      const b=await readJson(req,128*1024),old=readStoredSecrets();
      writeSecrets({
        ...old,
        openaiApiKey:b.openaiApiKey==="__KEEP__"?old.openaiApiKey:b.openaiApiKey,
        youtubeApiKey:b.youtubeApiKey==="__KEEP__"?old.youtubeApiKey:b.youtubeApiKey,
        driveClientId:b.driveClientId==="__KEEP__"?old.driveClientId:b.driveClientId,
        driveClientSecret:b.driveClientSecret==="__KEEP__"?old.driveClientSecret:b.driveClientSecret,
        driveFolderId:b.driveFolderId==="__KEEP__"?old.driveFolderId:b.driveFolderId,
        openaiModel:b.openaiModel||old.openaiModel||"gpt-5.6-luna",
        usdTry:b.usdTry??old.usdTry??48.12,
        monthlyBudgetTry:b.monthlyBudgetTry??old.monthlyBudgetTry??1000
      });
      return json(res,200,{ok:true,...integrationStatus()});
    }
    if(u.pathname==="/api/ai/ping"&&req.method==="POST") return await handleAiPing(req,res);
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
