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
function writeHomeworkDiagnostic(analysis={},cost=null,assignment=null){const safe={timestamp:new Date().toISOString(),assignmentId:assignment?.id??null,expectedStudentPages:Number(analysis.expectedStudentPages)||0,analyzedStudentPages:Array.isArray(analysis.analyzedStudentPages)?analysis.analyzedStudentPages.slice(0,500):[],missingStudentPages:Array.isArray(analysis.missingStudentPages)?analysis.missingStudentPages.slice(0,500):[],pdfCoverageVerified:!!analysis.pdfCoverageVerified,answerKeyFound:!!analysis.answerKeyFound,answerKeySource:String(analysis.answerKeySource||'none'),answerKeyConfidence:Number(analysis.answerKeyConfidence)||0,confidence:Number(analysis.confidence)||0,needsTeacherReview:!!analysis.needsTeacherReview,autoFinalize:!!analysis.autoFinalize,totalQuestions:Number(analysis.totalQuestions)||0,correct:Number(analysis.correct)||0,wrong:Number(analysis.wrong)||0,blank:Number(analysis.blank)||0,uncertain:Number(analysis.uncertain)||0,scorePercent:Number(analysis.scorePercent)||0,classifiedQuestions:Number(analysis.classifiedQuestions)||0,questionAccountingVerified:!!analysis.questionAccountingVerified,questionStatusConflictCount:Number(analysis.questionStatusConflictCount)||0,mathVerificationUsed:!!analysis.mathVerificationUsed,mathVerificationTargetCount:Number(analysis.mathVerificationTargetCount)||0,mathVerificationReviewedCount:Number(analysis.mathVerificationReviewedCount)||0,mathVerificationLowConfidenceCount:Number(analysis.mathVerificationLowConfidenceCount)||0,mathVerificationComplete:analysis.mathVerificationComplete===true,firstPassMs:Number(analysis.firstPassMs)||0,secondPassMs:Number(analysis.secondPassMs)||0,totalAnalysisMs:Number(analysis.totalAnalysisMs)||0,firstPassCostTry:Number(analysis.firstPassCostTry)||0,secondPassCostTry:Number(analysis.secondPassCostTry)||0,reviewReasons:Array.isArray(analysis.reviewReasons)?analysis.reviewReasons.slice(0,20):[],analysisArchitecture:String(analysis.analysisArchitecture||''),correctQuestionNumbers:Array.isArray(analysis.correctQuestionNumbers)?analysis.correctQuestionNumbers.slice(0,1000):[],wrongQuestionNumbers:Array.isArray(analysis.wrongQuestionNumbers)?analysis.wrongQuestionNumbers.slice(0,1000):[],blankQuestionNumbers:Array.isArray(analysis.blankQuestionNumbers)?analysis.blankQuestionNumbers.slice(0,1000):[],uncertainQuestionNumbers:Array.isArray(analysis.uncertainQuestionNumbers)?analysis.uncertainQuestionNumbers.slice(0,1000):[],costTry:Number(cost?.try)||0,secretsCollected:false,contentCollected:false};fs.mkdirSync(runtime,{recursive:true});fs.writeFileSync(path.join(runtime,'last_homework_analysis.json'),JSON.stringify(safe,null,2),'utf8');return safe}
function validateHomeworkQuestionAccounting(x={}){const total=Math.max(0,Math.round(Number(x.totalQuestions)||0)),correct=Math.max(0,Math.round(Number(x.correct)||0)),wrong=Math.max(0,Math.round(Number(x.wrong)||0)),blank=Math.max(0,Math.round(Number(x.blank)||0)),classifiedQuestions=correct+wrong+blank,questionAccountingVerified=total>0&&classifiedQuestions===total;const reviewRequired=!!x.needsTeacherReview||!questionAccountingVerified;return {...x,totalQuestions:total,correct,wrong,blank,classifiedQuestions,questionAccountingVerified,needsTeacherReview:reviewRequired,autoFinalize:!!x.autoFinalize&&!reviewRequired}}
function deriveHomeworkReviewReasons(x={}){const r=[];if(Number(x.confidence||0)<0.65)r.push('low_confidence');if(Number(x.totalQuestions||0)<=0)r.push('no_questions');if(x.questionCountMismatch)r.push('question_count_mismatch');if(x.questionAccountingVerified===false)r.push('question_accounting_mismatch');if(Number(x.questionStatusConflictCount||0)>0)r.push('question_status_conflict');if(x.pdfCoverageVerified===false)r.push('page_coverage_incomplete');if(String(x.answerKeySource||'')==='ambiguous')r.push('answer_key_ambiguous');if(x.answerKeyFound===false)r.push('answer_key_missing');if(x.answerKeyFound===true&&Number(x.answerKeyConfidence||0)<0.75)r.push('answer_key_low_confidence');if(!!x.needsTeacherReview&&!r.length)r.push('model_requested_review');return {...x,reviewReasons:[...new Set(r)].slice(0,20),needsTeacherReview:!!x.needsTeacherReview||r.length>0,autoFinalize:!!x.autoFinalize&&r.length===0}}
async function resolveStudentHomeworkFile(body={}){const source=String(body.studentFileSource||'local');if(source==='local'){if(!body.fileData)throw new Error('Ödev dosyası gerekli');return {source:'local',base64:body.fileData,mimeType:body.mimeType||'application/pdf',fileName:body.fileName||'odev.pdf',driveUsed:false}}if(source==='drive'){if(!body.studentDriveFileId)throw new Error('Drive ödev dosyası kimliği gerekli');const f=await driveDownloadAnalysisFile(body.studentDriveFileId);return {source:'drive',base64:f.base64,mimeType:f.mimeType||'application/pdf',fileName:body.fileName||'drive_odev.pdf',driveUsed:true}}throw new Error('Geçersiz ödev dosyası kaynağı')}
function homeworkReasoningInstruction(){return 'EL YAZISI ÇÖZÜM ANALİZİ PROTOKOLÜ: Her soruda yalnız son cevabı değil öğrencinin görülebilen el yazısı çözümünü de incele. approach alanında yöntemi özetle. stepsSummary görülen temel adımları sırayla vermeli. firstErrorStep ilk hatalı veya eksik adımı belirtir. errorCategory yalnız conceptual|arithmetic|attention|method|incomplete|none|uncertain değerlerinden biri olsun. conceptualIssue, arithmeticIssue ve attentionIssue alanlarını gerektiğinde doldur. methodQuality efficient|acceptable|inefficient|incorrect|uncertain olsun. Doğru sonuca hatalı veya tesadüfi yöntemle ulaşıldıysa note içinde açıkça belirt. unnecessarySteps ve missingSteps dizilerini üret. betterApproach daha uygun yöntemi kısa ve pedagojik biçimde açıklar. learningObjective tekrar edilmesi gereken kazanımı belirtir. solutionConfidence 0-1 arasıdır. El yazısı okunamıyorsa tahmin etme, uncertain yap. Üst düzey reasoningProfile içinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary üret.'}
function homeworkAssignmentScopeInstruction(){return `ATAMA SORU KAPSAMI PROTOKOLÜ:
Önce bu atamaya ait soru kümesini belirle; sonra yalnız bu kümeyi puanla ve çözüm yaklaşımını raporla. Kimlik olarak yalnız PDF üzerinde basılı/orijinal soru numaralarını kullan. Sayfada görünme sırası, kırpma sırası veya modelin kendi sayacı soru kimliği değildir. assignment.title, course, topic, resourceContext.title, unit, questionCount ve varsa test adı/başlığı ile eşleştir. PDF birden fazla test içeriyorsa yalnız atamaya ait testi seç. matchedQuestionNumbers benzersiz ve artan basılı soru numaraları olmalı. Beklenen questionCount varsa tam o kadar soru güvenle eşleşmedikçe assignmentMatchFound=false veya assignmentMatchConfidence düşük ver ve needsTeacherReview=true yap. Eşleşmeyen diğer testleri doğru/yanlış/boş toplamlarına katma. assignmentMatchEvidence hangi başlık/test/sayfa işaretleriyle eşleştiğini kısa açıklar.`}
function validateHomeworkAssignmentScope(analysis={},expected=0){const nums=Array.isArray(analysis.matchedQuestionNumbers)?analysis.matchedQuestionNumbers.map(Number).filter(n=>Number.isInteger(n)&&n>0):[];const unique=[...new Set(nums)].sort((a,b)=>a-b);const n=Math.max(0,Math.round(Number(expected)||0));const duplicateCount=Math.max(0,nums.length-unique.length);const confidence=Math.max(0,Math.min(1,Number(analysis.assignmentMatchConfidence)||0));const declared=analysis.assignmentMatchFound===true;const countOk=!n||unique.length===n;const found=declared&&duplicateCount===0&&countOk&&confidence>=0.75;return {...analysis,matchedQuestionNumbers:unique,matchedQuestionCount:unique.length,assignmentMatchConfidence:Math.round(confidence*1000)/1000,assignmentMatchFound:found,assignmentScopeDuplicateCount:duplicateCount,assignmentScopeCountVerified:countOk,assignmentMatchEvidence:String(analysis.assignmentMatchEvidence||'').slice(0,500),needsTeacherReview:!!analysis.needsTeacherReview||!found,autoFinalize:!!analysis.autoFinalize&&found}}
function lunaHomeworkDirectInstruction(){return `LUNA MALİYET-OPTİMİZE ÖDEV ANALİZ PROTOKOLÜ:
Yüklenen öğrenci PDF/görselinin tamamını doğrudan analiz et; ilk sayfada durma ve tüm fiziksel sayfaları sırayla tara.
ÖNCE PDF'deki bölüm/test başlıklarını belirle. Soru numaraları yeni bölüm/testte 1'den yeniden başlayabilir. Aynı basılı soru numarası farklı bölüm/testlerde FARKLI sorudur.
Soru kimliği kesinlikle yalnız basılı sayı değildir. Her fiziksel soru için sectionKey + printedNumber kullan. sectionKey aynı bölüm/test boyunca sabit, kısa ve benzersiz olsun. Örnek: sayi-problemleri:1, kesir-problemleri:1 ve bos-dolu-problemleri:1 üç ayrı sorudur. Başlık yoksa fallback olarak page<sayfa>:q<basılıNo> kullan. Kesme/görünme sırasını kimlik yapma.
DOĞRU sorular için yalnız {sectionKey,section,page,printedNumber} kaydını correctQuestions listesine yaz; çözüm açıklaması üretme.
BOŞ sorular için yalnız aynı kimlik alanlarını blankQuestions listesine yaz; neden tahmini yapma.
UNCERTAIN sorular için yalnız aynı kimlik alanlarını uncertainQuestions listesine yaz; tahmin yapma.
YALNIZ WRONG sorular için items içinde kimlik alanlarıyla birlikte studentAnswer, correctAnswer, approach, stepsSummary, firstErrorStep, errorCategory, conceptualIssue, arithmeticIssue, attentionIssue, methodQuality, unnecessarySteps, missingSteps, betterApproach, learningObjective, solutionConfidence ve kısa note üret.
El yazısında ilk yanlış adımı özellikle bul. PDF içinde güvenilir basılı cevap anahtarı varsa yerini answerKeyEvidence ile belirt. Güvenilir anahtar yoksa doğru/yanlış uydurma; uncertain yap.
reasoningProfile yalnız WRONG sorulardan türetilsin ve kısa olsun.
`}
function validateLunaQuestionAccounting(x={}){const items=Array.isArray(x.items)?x.items:[];const uncertainField=Math.max(0,Math.round(Number(x.uncertain)||0));const uncertainFromItems=items.filter(i=>String(i?.status||'')==='uncertain').length;const uncertain=Math.max(uncertainField,uncertainFromItems);const correct=Math.max(0,Math.round(Number(x.correct)||0)),wrong=Math.max(0,Math.round(Number(x.wrong)||0)),blank=Math.max(0,Math.round(Number(x.blank)||0)),total=Math.max(0,Math.round(Number(x.totalQuestions)||0));const classified=correct+wrong+blank+uncertain;const ok=total>0&&classified===total;return {...x,uncertain,classifiedQuestions:classified,questionAccountingVerified:ok,needsTeacherReview:!!x.needsTeacherReview||!ok,autoFinalize:!!x.autoFinalize&&ok}}
function validateLunaDirectAnswerKey(x={},manualAnswerKey=null){const manual=String(manualAnswerKey||'').trim();if(manual)return {...x,answerKeyFound:true,answerKeySource:'manual',answerKeyOriginDocument:'manual',answerKeyConfidence:1};const source=String(x.answerKeySource||'none'),origin=String(x.answerKeyOriginDocument||'none'),confidence=Math.max(0,Math.min(1,Number(x.answerKeyConfidence)||0));const embedded=['embedded_same_page','embedded_adjacent_page','embedded_end_pages'].includes(source)&&origin==='student_pdf'&&x.answerKeyFound===true;const valid=embedded&&confidence>=0.75;return {...x,answerKeyFound:embedded,answerKeySource:embedded?source:(source==='ambiguous'?'ambiguous':'none'),answerKeyOriginDocument:embedded?'student_pdf':(source==='ambiguous'?'ambiguous':'none'),answerKeyConfidence:confidence,needsTeacherReview:!!x.needsTeacherReview||!valid,autoFinalize:!!x.autoFinalize&&valid}}
function normalizeQuestionNumberList(a){return Array.isArray(a)?[...new Set(a.map(Number).filter(n=>Number.isInteger(n)&&n>0))].sort((x,y)=>x-y).slice(0,1000):[]}
function normalizeHomeworkQuestionRef(x={}){const printedNumber=Math.max(0,Math.round(Number(x.printedNumber??x.question)||0)),page=Math.max(0,Math.round(Number(x.page)||0)),section=String(x.section||'').trim().slice(0,160),rawKey=String(x.sectionKey||section||'').trim().toLocaleLowerCase('tr-TR').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9ıüğşöç]+/g,'-').replace(/^-+|-+$/g,'').slice(0,120),sectionKey=rawKey||('page'+(page||0));if(!printedNumber)return null;const questionId=sectionKey+':'+printedNumber,label=(section||sectionKey)+' / Soru '+printedNumber;return {questionId,sectionKey,section,page,printedNumber,label}}
function normalizeHomeworkQuestionRefs(a=[]){const out=[],seen=new Set();for(const x of Array.isArray(a)?a:[]){const q=normalizeHomeworkQuestionRef(x);if(q&&!seen.has(q.questionId)){seen.add(q.questionId);out.push(q)}}return out}
function finalizeHomeworkQuestionSets(x={}){const rawCorrect=normalizeHomeworkQuestionRefs(x.correctQuestions),rawBlank=normalizeHomeworkQuestionRefs(x.blankQuestions),rawUncertain=normalizeHomeworkQuestionRefs(x.uncertainQuestions),rawItems=[];for(const z of Array.isArray(x.items)?x.items:[]){if(String(z?.status||'wrong')!=='wrong')continue;const q=normalizeHomeworkQuestionRef(z);if(q)rawItems.push({...z,...q,question:q.printedNumber,questionLabel:q.label,status:'wrong'})}const rawWrong=normalizeHomeworkQuestionRefs(rawItems);const byId=new Map(),add=(status,list)=>{for(const q of list){const row=byId.get(q.questionId)||{ref:q,statuses:new Set()};row.statuses.add(status);byId.set(q.questionId,row)}};add('correct',rawCorrect);add('wrong',rawWrong);add('blank',rawBlank);add('uncertain',rawUncertain);const correctQuestions=[],wrongQuestions=[],blankQuestions=[],uncertainQuestions=[],conflicts=[];for(const [id,row] of byId){const statuses=[...row.statuses];if(statuses.length>1){uncertainQuestions.push(row.ref);conflicts.push({questionId:id,label:row.ref.label,statuses:statuses.sort()});continue}const st=statuses[0];if(st==='correct')correctQuestions.push(row.ref);else if(st==='wrong')wrongQuestions.push(row.ref);else if(st==='blank')blankQuestions.push(row.ref);else uncertainQuestions.push(row.ref)}const wrongIds=new Set(wrongQuestions.map(q=>q.questionId)),items=rawItems.filter(z=>wrongIds.has(z.questionId));const correct=correctQuestions.length,wrong=wrongQuestions.length,blank=blankQuestions.length,uncertain=uncertainQuestions.length,total=byId.size,classified=correct+wrong+blank+uncertain,statusConflictCount=conflicts.length,accountingOk=total>0&&classified===total,statusOk=statusConflictCount===0,score=total?Math.round(1000*correct/total)/10:0;return {...x,correctQuestions,wrongQuestions,blankQuestions,uncertainQuestions,items,correct,wrong,blank,uncertain,totalQuestions:total,classifiedQuestions:classified,scorePercent:score,questionIdentityDuplicateCount:0,questionStatusConflictCount:statusConflictCount,questionStatusConflicts:conflicts,questionStatusVerified:statusOk,questionAccountingVerified:accountingOk,correctQuestionNumbers:correctQuestions.map(q=>q.label),wrongQuestionNumbers:wrongQuestions.map(q=>q.label),blankQuestionNumbers:blankQuestions.map(q=>q.label),uncertainQuestionNumbers:uncertainQuestions.map(q=>q.label),needsTeacherReview:!!x.needsTeacherReview||!accountingOk||!statusOk,autoFinalize:!!x.autoFinalize&&accountingOk&&statusOk}}
function homeworkMathVerificationInstruction(){return `LUNA MATEMATİK İKİNCİ GEÇİŞ PROTOKOLÜ:
Bu çağrıda yalnız verilen hedef soruları yeniden incele. PDF'nin diğer sorularını raporlama.
Her hedef için sectionKey, section, page ve printedNumber kimliğini aynen koru. Önce öğrencinin görünür el yazısındaki matematiksel ifadeleri SATIR SATIR transkribe et. +, -, ×, ÷, /, =, <, >, ≤, ≥, parantez, üs, kök, kesir çizgisi ve değişken sembollerini dikkatle ayır.
Okunamayan sembolü tahmin etme; transcriptionLines içinde [BELİRSİZ] yaz ve symbolConfidence değerini düşür.
Transkripsiyon tamamlanmadan matematiksel yorum yapma. Ardından satırlar arasındaki işlemleri yeniden hesapla ve finalStatus değerini correct|wrong|blank|uncertain olarak ver.
Yanlışsa firstErrorStep ilk gerçekten hatalı matematik adımı olmalı. errorCategory conceptual|arithmetic|attention|method|incomplete|uncertain değerlerinden biri olsun. betterApproach kısa ve matematiksel olarak doğru çözüm yolunu versin.
Sembol güveni 0.75 altındaysa finalStatus=uncertain yap; kesin hüküm verme.
Yalnız geçerli kısa JSON döndür.
`}
function homeworkMathVerificationTargets(x={}){const out=[],seen=new Set();for(const q of [...(Array.isArray(x.wrongQuestions)?x.wrongQuestions:[]),...(Array.isArray(x.uncertainQuestions)?x.uncertainQuestions:[])]){const n=normalizeHomeworkQuestionRef(q);if(n&&!seen.has(n.questionId)){seen.add(n.questionId);out.push(n)}}return out.slice(0,80)}
function applyHomeworkMathVerification(x={},reviews=[]){const targets=new Set(homeworkMathVerificationTargets(x).map(q=>q.questionId)),verified=new Map();for(const r of Array.isArray(reviews)?reviews:[]){const q=normalizeHomeworkQuestionRef(r);if(!q||!targets.has(q.questionId))continue;const symbolConfidence=Math.max(0,Math.min(1,Number(r.symbolConfidence)||0)),raw=String(r.finalStatus||'uncertain'),finalStatus=symbolConfidence>=0.75&&['correct','wrong','blank'].includes(raw)?raw:'uncertain';verified.set(q.questionId,{...r,...q,finalStatus,symbolConfidence,status:finalStatus==='wrong'?'wrong':finalStatus,question:q.printedNumber,questionLabel:q.label})}const correctQuestions=[...(x.correctQuestions||[])],blankQuestions=[...(x.blankQuestions||[])],uncertainQuestions=[],items=[];for(const q of homeworkMathVerificationTargets(x)){const v=verified.get(q.questionId);if(!v){uncertainQuestions.push(q);continue}if(v.finalStatus==='correct')correctQuestions.push(q);else if(v.finalStatus==='blank')blankQuestions.push(q);else if(v.finalStatus==='wrong')items.push(v);else uncertainQuestions.push(q)}const merged=finalizeHomeworkQuestionSets({...x,correctQuestions,blankQuestions,uncertainQuestions,items});const reviewed=verified.size,low=[...verified.values()].filter(v=>v.symbolConfidence<0.75||v.finalStatus==='uncertain').length,targetCount=targets.size,complete=reviewed===targetCount&&low===0;return {...merged,mathVerificationTargetCount:targetCount,mathVerificationReviewedCount:reviewed,mathVerificationLowConfidenceCount:low,mathVerificationComplete:complete,mathVerificationUsed:targetCount>0,needsTeacherReview:!!merged.needsTeacherReview||!complete,autoFinalize:!!merged.autoFinalize&&complete}}
async function handleHomework(req,res){
  const totalStarted=Date.now(),body=await readJson(req,18*1024*1024);
  const {assignment,answerKey=null,resourceContext=null,studentFileSource="local"}=body;
  let studentFile;try{studentFile=await resolveStudentHomeworkFile(body)}catch(e){return json(res,400,{ok:false,error:e.message})}
  if(!integrationStatus().openai.configured)return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const expectedStudentPages=estimatePdfPageCount(studentFile.base64,studentFile.mimeType);
  const safeContext=resourceContext?{resourceId:resourceContext.resourceId||null,course:resourceContext.course||assignment?.course||"",unit:resourceContext.unit||"",topic:resourceContext.topic||assignment?.topic||"",level:resourceContext.level||"",title:resourceContext.title||assignment?.title||""}:null;
  const meta={assignment:{id:assignment?.id||null,course:assignment?.course||"",topic:assignment?.topic||"",title:assignment?.title||""},resourceContext:safeContext,manualAnswerKey:answerKey||null};
  const firstStarted=Date.now();
  const firstContent=[{type:"input_text",text:JSON.stringify(meta)},{type:"input_text",text:"BİRİNCİ GEÇİŞ: Tüm sayfaları tara; bölüm/test ve soru kimliklerini koru. Sadece doğru/yanlış/boş/belirsiz sınıflaması yap. Yanlış çözüm ayrıntısını bu geçişte üretme."},{type:"input_file",filename:studentFile.fileName,file_data:"data:"+studentFile.mimeType+";base64,"+studentFile.base64}];
  const firstAi=await openaiRequest({instructions:lunaHomeworkDirectInstruction()+"\nSadece geçerli ve KISA JSON döndür. Şema: {\"confidence\":number,\"needsTeacherReview\":boolean,\"correctQuestions\":[{\"sectionKey\":\"string\",\"section\":\"string\",\"page\":number,\"printedNumber\":number}],\"blankQuestions\":[aynı kimlik],\"uncertainQuestions\":[aynı kimlik],\"items\":[{\"sectionKey\":\"string\",\"section\":\"string\",\"page\":number,\"printedNumber\":number,\"status\":\"wrong\"}],\"reasoningProfile\":{\"strengths\":[],\"recurringErrors\":[],\"conceptualGaps\":[],\"proceduralGaps\":[],\"attentionPatterns\":[],\"recommendedActions\":[],\"summary\":\"\"},\"summary\":\"string\",\"answerKeyFound\":boolean,\"answerKeySource\":\"manual|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none\",\"answerKeyOriginDocument\":\"manual|student_pdf|ambiguous|none\",\"answerKeyConfidence\":number,\"answerKeyEvidence\":\"string\",\"analyzedStudentPages\":[number]}",input:[{role:"user",content:firstContent}],reasoning:"low"});
  const firstPassMs=Date.now()-firstStarted;
  let parsed=normalizeHomeworkAnalysis(parseJsonText(firstAi.text));
  parsed=finalizeHomeworkQuestionSets(parsed);
  parsed=validateLunaDirectAnswerKey(parsed,answerKey);
  parsed=validateHomeworkPageCoverage(parsed,expectedStudentPages,0);
  parsed=validateLunaQuestionAccounting(parsed);
  parsed=deriveHomeworkReviewReasons(parsed);
  const firstCost=appendUsage("homework_scan",firstAi.model,firstAi.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  const targets=homeworkMathVerificationTargets(parsed);
  let secondAi=null,secondCost=null,secondPassMs=0;
  if(targets.length){
    const secondStarted=Date.now(),targetMeta=targets.map(q=>({sectionKey:q.sectionKey,section:q.section,page:q.page,printedNumber:q.printedNumber,questionId:q.questionId}));
    const secondContent=[{type:"input_text",text:JSON.stringify({targets:targetMeta,manualAnswerKey:answerKey||null})},{type:"input_text",text:"İKİNCİ GEÇİŞ: Yalnız targets listesindeki soruları PDF içinde yeniden bul. Önce el yazısı matematik satırlarını ve sembolleri transkribe et, sonra işlemleri doğrula."},{type:"input_file",filename:studentFile.fileName,file_data:"data:"+studentFile.mimeType+";base64,"+studentFile.base64}];
    secondAi=await openaiRequest({instructions:homeworkMathVerificationInstruction()+"\nYalnız JSON: {\"reviews\":[{\"sectionKey\":\"string\",\"section\":\"string\",\"page\":number,\"printedNumber\":number,\"finalStatus\":\"correct|wrong|blank|uncertain\",\"transcriptionLines\":[\"string\"],\"symbolConfidence\":number,\"studentAnswer\":\"string|null\",\"correctAnswer\":\"string|null\",\"approach\":\"string|null\",\"stepsSummary\":[\"string\"],\"firstErrorStep\":\"string|null\",\"errorCategory\":\"conceptual|arithmetic|attention|method|incomplete|uncertain\",\"conceptualIssue\":\"string|null\",\"arithmeticIssue\":\"string|null\",\"attentionIssue\":\"string|null\",\"methodQuality\":\"efficient|acceptable|inefficient|incorrect|uncertain\",\"unnecessarySteps\":[\"string\"],\"missingSteps\":[\"string\"],\"betterApproach\":\"string|null\",\"learningObjective\":\"string|null\",\"solutionConfidence\":number,\"note\":\"string|null\"}]}",input:[{role:"user",content:secondContent}],reasoning:"low"});
    secondPassMs=Date.now()-secondStarted;
    const secondParsed=parseJsonText(secondAi.text);
    parsed=applyHomeworkMathVerification(parsed,secondParsed.reviews);
    parsed=validateLunaQuestionAccounting(parsed);
    parsed=deriveHomeworkReviewReasons(parsed);
    secondCost=appendUsage("homework_math_verify",secondAi.model,secondAi.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null,targetCount:targets.length});
  }else{parsed={...parsed,mathVerificationTargetCount:0,mathVerificationReviewedCount:0,mathVerificationLowConfidenceCount:0,mathVerificationComplete:true,mathVerificationUsed:false}}
  const totalMs=Date.now()-totalStarted,cost={try:Number(firstCost?.try||0)+Number(secondCost?.try||0),usd:Number(firstCost?.usd||0)+Number(secondCost?.usd||0),firstPass:firstCost,secondPass:secondCost};
  parsed.studentFileSource=studentFileSource;parsed.studentFileDriveUsed=!!studentFile.driveUsed;parsed.analysisArchitecture="two_pass_luna_math_verification";parsed.firstPassMs=firstPassMs;parsed.secondPassMs=secondPassMs;parsed.totalAnalysisMs=totalMs;parsed.firstPassCostTry=Number(firstCost?.try||0);parsed.secondPassCostTry=Number(secondCost?.try||0);
  writeHomeworkDiagnostic(parsed,cost,assignment);
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:{firstPass:firstAi.data?.usage||null,secondPass:secondAi?.data?.usage||null},cost});
}

function reportText(v,max=1200){return String(v==null?'':v).replace(/[\u0000-\u001f\u007f]/g,' ').trim().slice(0,max)}
function reportNums(a){return Array.isArray(a)?[...new Set(a.map(v=>String(v||'').trim()).filter(Boolean))].slice(0,1000):[]}
function sanitizeHomeworkReportPayload(body={}){const x=body.analysis||{},rp=x.reasoningProfile||{},arr=(v,n=20)=>Array.isArray(v)?v.slice(0,n).map(z=>reportText(z,300)).filter(Boolean):[];const items=(Array.isArray(x.items)?x.items:[]).filter(z=>String(z?.status||'wrong')==='wrong').slice(0,200).map(z=>({question:reportText(z.questionLabel||z.question,180),studentAnswer:reportText(z.studentAnswer,120),correctAnswer:reportText(z.correctAnswer,120),approach:reportText(z.approach,500),stepsSummary:arr(z.stepsSummary,12),firstErrorStep:reportText(z.firstErrorStep,500),errorCategory:reportText(z.errorCategory,80),betterApproach:reportText(z.betterApproach,700),learningObjective:reportText(z.learningObjective,300),note:reportText(z.note,500)}));return {student:{name:reportText(body.student?.name,160),grade:reportText(body.student?.grade,80)},assignment:{title:reportText(body.assignment?.title,220),course:reportText(body.assignment?.course,120),topic:reportText(body.assignment?.topic,180),date:reportText(body.assignment?.date,40)},analysis:{totalQuestions:Number(x.totalQuestions)||0,correct:Number(x.correct)||0,wrong:Number(x.wrong)||0,blank:Number(x.blank)||0,uncertain:Number(x.uncertain)||0,scorePercent:Number(x.scorePercent)||0,correctQuestionNumbers:reportNums(x.correctQuestionNumbers),blankQuestionNumbers:reportNums(x.blankQuestionNumbers),uncertainQuestionNumbers:reportNums(x.uncertainQuestionNumbers),items,reasoningProfile:{recurringErrors:arr(rp.recurringErrors),conceptualGaps:arr(rp.conceptualGaps),proceduralGaps:arr(rp.proceduralGaps),attentionPatterns:arr(rp.attentionPatterns),recommendedActions:arr(rp.recommendedActions),summary:reportText(rp.summary||x.summary,1600)}},costTry:Number(body.costTry)||0}}
function reportHtmlEscape(v){return reportText(v,5000).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
function buildHomeworkReportHtml(r){const e=reportHtmlEscape,nums=v=>v?.length?v.join(', '):'—',list=v=>v?.length?v.map(e).join(', '):'—';const rows=r.analysis.items.map(z=>'<tr><td>'+e(z.question)+'</td><td>'+e(z.studentAnswer||'—')+'</td><td>'+e(z.correctAnswer||'—')+'</td><td>'+e(z.errorCategory||'—')+'</td><td>'+e(z.firstErrorStep||'—')+'</td><td>'+e(z.learningObjective||'—')+'</td></tr>').join('')||'<tr><td colspan="6">Yanlış soru bulunmadı.</td></tr>';const det=r.analysis.items.map(z=>'<h3>Soru '+e(z.question)+'</h3><table><tr><th>Öğrenci cevabı</th><td>'+e(z.studentAnswer||'—')+'</td><th>Doğru cevap</th><td>'+e(z.correctAnswer||'—')+'</td></tr><tr><th>Yaklaşım</th><td colspan="3">'+e(z.approach||'—')+'</td></tr><tr><th>İlk hata</th><td colspan="3">'+e(z.firstErrorStep||'—')+'</td></tr><tr><th>Hata türü</th><td>'+e(z.errorCategory||'—')+'</td><th>Kazanım</th><td>'+e(z.learningObjective||'—')+'</td></tr><tr><th>Daha iyi yaklaşım</th><td colspan="3">'+e(z.betterApproach||'—')+'</td></tr><tr><th>Çözüm adımları</th><td colspan="3">'+e((z.stepsSummary||[]).join(' → ')||'—')+'</td></tr></table>').join('');return '<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>YILBAY Ödev Analiz Karnesi</title><style>@page{size:A4;margin:12mm}body{font-family:Arial,sans-serif;color:#172033;font-size:10pt;line-height:1.4}h1{font-size:20pt;border-bottom:3px solid #243b64;padding-bottom:7px}h2{font-size:14pt;border-bottom:2px solid #243b64;padding-bottom:4px;margin-top:18px}h3{font-size:12pt;break-after:avoid}.meta,.stats,table{width:100%;border-collapse:collapse;margin:7px 0 12px}th,td{border:1px solid #cbd3df;padding:6px;vertical-align:top;word-break:break-word}th{background:#eef2f7;text-align:left}.stats td{text-align:center;font-size:11pt}.stats b{display:block;font-size:17pt}.detail{break-inside:avoid}.footer{font-size:8.5pt;color:#667085;border-top:1px solid #ddd;margin-top:18px;padding-top:6px}</style></head><body><h1>YILBAY – Ödev Analiz Karnesi</h1><table class="meta"><tr><th>Öğrenci</th><td>'+e(r.student.name||'—')+'</td><th>Sınıf</th><td>'+e(r.student.grade||'—')+'</td></tr><tr><th>Ders</th><td>'+e(r.assignment.course||'—')+'</td><th>Konu</th><td>'+e(r.assignment.topic||'—')+'</td></tr><tr><th>Ödev</th><td>'+e(r.assignment.title||'—')+'</td><th>Tarih</th><td>'+e(r.assignment.date||'—')+'</td></tr></table><table class="stats"><tr><td><b>'+e(r.analysis.totalQuestions)+'</b>Toplam</td><td><b>'+e(r.analysis.correct)+'</b>Doğru</td><td><b>'+e(r.analysis.wrong)+'</b>Yanlış</td><td><b>'+e(r.analysis.blank)+'</b>Boş</td><td><b>%'+e(Math.round(r.analysis.scorePercent*10)/10)+'</b>Başarı</td></tr></table><h2>Soru Durumları</h2><table><tr><th>Doğru</th><td>'+nums(r.analysis.correctQuestionNumbers)+'</td></tr><tr><th>Yanlış</th><td>'+nums(r.analysis.items.map(z=>z.question))+'</td></tr><tr><th>Boş</th><td>'+nums(r.analysis.blankQuestionNumbers)+'</td></tr><tr><th>Belirsiz</th><td>'+nums(r.analysis.uncertainQuestionNumbers)+'</td></tr></table><h2>Yanlış Sorular – Özet Tablo</h2><table><tr><th>Soru</th><th>Öğrenci</th><th>Doğru</th><th>Hata Türü</th><th>İlk Hata</th><th>Kazanım</th></tr>'+rows+'</table><h2>Yanlış Sorular – Ayrıntılı Analiz</h2>'+det+'<h2>Pedagojik Karne</h2><table><tr><th>Tekrarlayan hatalar</th><td>'+list(r.analysis.reasoningProfile.recurringErrors)+'</td></tr><tr><th>Kavramsal eksikler</th><td>'+list(r.analysis.reasoningProfile.conceptualGaps)+'</td></tr><tr><th>İşlem/prosedür eksikleri</th><td>'+list(r.analysis.reasoningProfile.proceduralGaps)+'</td></tr><tr><th>Dikkat örüntüleri</th><td>'+list(r.analysis.reasoningProfile.attentionPatterns)+'</td></tr><tr><th>Önerilen çalışma</th><td>'+list(r.analysis.reasoningProfile.recommendedActions)+'</td></tr><tr><th>Genel değerlendirme</th><td>'+e(r.analysis.reasoningProfile.summary||'—')+'</td></tr></table><div class="footer">PDF yerel olarak oluşturuldu · Ek AI maliyeti yok · Analiz maliyeti '+e(r.costTry.toFixed(4))+' TL</div></body></html>'}
function findHomeworkPdfBrowser(){const c=[process.env.YILBAY_BROWSER_PATH,process.env.ProgramFiles&&path.join(process.env.ProgramFiles,'Google/Chrome/Application/chrome.exe'),process.env.ProgramFiles&&path.join(process.env.ProgramFiles,'Microsoft/Edge/Application/msedge.exe'),process.env['ProgramFiles(x86)']&&path.join(process.env['ProgramFiles(x86)'],'Microsoft/Edge/Application/msedge.exe')].filter(Boolean);return c.find(v=>fs.existsSync(v))||null}
function generateHomeworkReportPdf(r){const browser=findHomeworkPdfBrowser();if(!browser)throw new Error('PDF oluşturmak için Chrome/Edge bulunamadı');const dir=path.join(runtime,'homework_reports');fs.mkdirSync(dir,{recursive:true});const id=String(Date.now())+'_'+Math.random().toString(16).slice(2,10),html=path.join(dir,id+'.html'),pdf=path.join(dir,id+'.pdf');fs.writeFileSync(html,buildHomeworkReportHtml(r),'utf8');const u=encodeURI('file:///'+html.split(path.sep).join('/')),profile=path.join(runtime,'pdf_browser_profile'),args=['--disable-gpu','--no-pdf-header-footer','--user-data-dir='+profile,'--print-to-pdf='+pdf,u];let z=cp.spawnSync(browser,['--headless=new',...args],{encoding:'utf8',windowsHide:true,timeout:45000});if(z.status!==0||!fs.existsSync(pdf))z=cp.spawnSync(browser,['--headless',...args],{encoding:'utf8',windowsHide:true,timeout:45000});fs.rmSync(html,{force:true});if(z.status!==0||!fs.existsSync(pdf)||fs.statSync(pdf).size<1000)throw new Error('PDF karne oluşturulamadı');if(fs.readFileSync(pdf).subarray(0,5).toString('ascii')!=='%PDF-')throw new Error('PDF çıktı doğrulanamadı');return {reportId:id,downloadUrl:'/api/reports/homework-pdf/'+id,size:fs.statSync(pdf).size}}
async function handleHomeworkReportPdf(req,res){try{const body=await readJson(req,1024*1024),safe=sanitizeHomeworkReportPayload(body),out=generateHomeworkReportPdf(safe);writeHomeworkPdfDiagnostic({generated:true,reportId:out.reportId,sizeBytes:out.size});return json(res,200,{ok:true,...out})}catch(e){writeHomeworkPdfDiagnostic({generated:false,error:e.message||'PDF karne oluşturulamadı'});return json(res,500,{ok:false,error:e.message||'PDF karne oluşturulamadı'})}}
function writeHomeworkPdfDiagnostic(x={}){const safe={timestamp:new Date().toISOString(),generated:x.generated===true,reportId:String(x.reportId||'').slice(0,80),sizeBytes:Math.max(0,Number(x.sizeBytes)||0),error:String(x.error||'').slice(0,300),secretsCollected:false,contentCollected:false};fs.mkdirSync(runtime,{recursive:true});fs.writeFileSync(path.join(runtime,'last_homework_pdf.json'),JSON.stringify(safe,null,2),'utf8');return safe}
function handleHomeworkReportDelete(u,res){const m=String(u.pathname||'').match(/^\/api\/reports\/homework-pdf\/([0-9]+_[a-f0-9]{1,16})$/i);if(!m)return json(res,400,{ok:false,error:'Geçersiz PDF kimliği'});const f=path.join(runtime,'homework_reports',m[1]+'.pdf');fs.rmSync(f,{force:true});return json(res,200,{ok:true,deleted:true})}
function handleHomeworkReportDownload(u,res){const m=String(u.pathname||'').match(/^\/api\/reports\/homework-pdf\/([0-9]+_[a-f0-9]{1,16})$/i);if(!m){res.writeHead(404);return res.end('Not found')}const f=path.join(runtime,'homework_reports',m[1]+'.pdf');if(!fs.existsSync(f)){res.writeHead(404);return res.end('Not found')}const d=fs.readFileSync(f);res.writeHead(200,{'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="YILBAY_Odev_Analiz_Karnesi.pdf"','Content-Length':d.length,'Cache-Control':'no-store'});return res.end(d)}

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
    if(u.pathname==="/health") return json(res,200,{ok:true,version:"0.11.0",integrations:integrationStatus()});
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
    if(u.pathname==="/api/reports/homework-pdf"&&req.method==="POST") return await handleHomeworkReportPdf(req,res);
    if(u.pathname.startsWith("/api/reports/homework-pdf/")&&req.method==="DELETE") return handleHomeworkReportDelete(u,res);
    if(u.pathname.startsWith("/api/reports/homework-pdf/")&&req.method==="GET") return handleHomeworkReportDownload(u,res);
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
