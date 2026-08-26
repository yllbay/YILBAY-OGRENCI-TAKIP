import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay0105';
const mp=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(mp,'utf8'));
if(m.version!=='0.10.4'||m.protocol!=='micro-cell-v2-ast')throw new Error('Expected verified v0.10.4 source');
for(const e of [...m.frontend,...m.backend]){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.10.4','0.10.5');fs.writeFileSync(p,s,'utf8')}
const byName=(arr,n)=>arr.find(x=>x.name===n);
const handle=byName(m.backend,'handleHomework'),submit=byName(m.frontend,'submitHomeworkAnalysis'),analyze=byName(m.frontend,'analyzeAssignment');
if(!handle||!submit||!analyze)throw new Error('Required cells missing');
const hp=path.join(ROOT,handle.file);
const directInstruction="function lunaHomeworkDirectInstruction(){return `LUNA DOĞRUDAN ÖDEV ANALİZ PROTOKOLÜ:\nYüklenen öğrenci PDF/görselinin tamamını doğrudan analiz et. Programın yerel tahminlerine güvenme; belgeyi kendin incele. İlk sayfada durma, tüm sayfaları sırayla tara.\nHer basılı soru için soru numarasını, öğrencinin cevabını, doğru cevabı yalnız güvenilir cevap anahtarı varsa, correct|wrong|blank|uncertain durumunu ve el yazısı çözümünü değerlendir.\nEl yazısında öğrencinin yaklaşımını, görülen çözüm adımlarını, ilk hata adımını, kavramsal/işlem/dikkat/yöntem/eksik çözüm hatasını, gereksiz ve eksik adımları, yöntem kalitesini, daha iyi yaklaşımı ve tekrar edilmesi gereken kazanımı çıkar.\nDoğru sonuca hatalı yöntemle gelindiyse bunu açıkça belirt. Okunamayan el yazısını tahmin etme.\nPDF içinde basılı bir cevap anahtarı varsa yerini ve bunun öğrenci işaretlerinden neden ayrı olduğunu answerKeyEvidence alanında belirt. Manuel cevap anahtarı verilmişse onu kullan. Güvenilir cevap anahtarı yoksa doğru/yanlış uydurma; ilgili soruları uncertain yap ve needsTeacherReview=true üret.\nBelgede birden fazla test varsa hepsini belge kapsamında analiz et; program dışarıdan soru sayısı dayatmayacak. Soru kimliği yalnız basılı/orijinal soru numarasıdır.\nÜst düzey öğrenci karnesinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary üret.\n`}\n";
const accounting="function validateLunaQuestionAccounting(x={}){const items=Array.isArray(x.items)?x.items:[];const uncertainField=Math.max(0,Math.round(Number(x.uncertain)||0));const uncertainFromItems=items.filter(i=>String(i?.status||'')==='uncertain').length;const uncertain=Math.max(uncertainField,uncertainFromItems);const correct=Math.max(0,Math.round(Number(x.correct)||0)),wrong=Math.max(0,Math.round(Number(x.wrong)||0)),blank=Math.max(0,Math.round(Number(x.blank)||0)),total=Math.max(0,Math.round(Number(x.totalQuestions)||0));const classified=correct+wrong+blank+uncertain;const ok=total>0&&classified===total;return {...x,uncertain,classifiedQuestions:classified,questionAccountingVerified:ok,needsTeacherReview:!!x.needsTeacherReview||!ok,autoFinalize:!!x.autoFinalize&&ok}}\n";
const keyValidator="function validateLunaDirectAnswerKey(x={},manualAnswerKey=null){const manual=String(manualAnswerKey||'').trim();if(manual)return {...x,answerKeyFound:true,answerKeySource:'manual',answerKeyOriginDocument:'manual',answerKeyConfidence:1};const source=String(x.answerKeySource||'none'),origin=String(x.answerKeyOriginDocument||'none'),confidence=Math.max(0,Math.min(1,Number(x.answerKeyConfidence)||0));const embedded=['embedded_same_page','embedded_adjacent_page','embedded_end_pages'].includes(source)&&origin==='student_pdf'&&x.answerKeyFound===true;const valid=embedded&&confidence>=0.75;return {...x,answerKeyFound:embedded,answerKeySource:embedded?source:(source==='ambiguous'?'ambiguous':'none'),answerKeyOriginDocument:embedded?'student_pdf':(source==='ambiguous'?'ambiguous':'none'),answerKeyConfidence:confidence,needsTeacherReview:!!x.needsTeacherReview||!valid,autoFinalize:!!x.autoFinalize&&valid}}\n";
let hs=fs.readFileSync(hp,'utf8');
const start=hs.indexOf('async function handleHomework(req,res){');
const end=hs.indexOf('\n\n/* CELL:60-youtube',start);
if(start<0||end<0)throw new Error('handle bounds missing');
const schema='Sadece geçerli JSON döndür. Şema: {"totalQuestions":number,"correct":number,"wrong":number,"blank":number,"uncertain":number,"scorePercent":number,"confidence":number,"needsTeacherReview":boolean,"items":[{"question":number,"status":"correct|wrong|blank|uncertain","studentAnswer":"string|null","correctAnswer":"string|null","approach":"string|null","stepsSummary":["string"],"firstErrorStep":"string|null","errorCategory":"conceptual|arithmetic|attention|method|incomplete|none|uncertain","conceptualIssue":"string|null","arithmeticIssue":"string|null","attentionIssue":"string|null","methodQuality":"efficient|acceptable|inefficient|incorrect|uncertain","unnecessarySteps":["string"],"missingSteps":["string"],"betterApproach":"string|null","learningObjective":"string|null","solutionConfidence":number,"note":"string|null"}],"reasoningProfile":{"strengths":["string"],"recurringErrors":["string"],"conceptualGaps":["string"],"proceduralGaps":["string"],"attentionPatterns":["string"],"recommendedActions":["string"],"summary":"string"},"weaknesses":["string"],"summary":"string","answerKeyFound":boolean,"answerKeySource":"manual|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none","answerKeyOriginDocument":"manual|student_pdf|ambiguous|none","answerKeyConfidence":number,"answerKeyEvidence":"string","analyzedStudentPages":[number]}';
const lines=[
'async function handleHomework(req,res){',
'  const body=await readJson(req,18*1024*1024);',
'  const {assignment,answerKey=null,resourceContext=null,studentFileSource="local"}=body;',
'  let studentFile;try{studentFile=await resolveStudentHomeworkFile(body)}catch(e){return json(res,400,{ok:false,error:e.message})}',
'  if(!integrationStatus().openai.configured)return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});',
'  const expectedStudentPages=estimatePdfPageCount(studentFile.base64,studentFile.mimeType);',
'  const safeContext=resourceContext?{resourceId:resourceContext.resourceId||null,course:resourceContext.course||assignment?.course||"",unit:resourceContext.unit||"",topic:resourceContext.topic||assignment?.topic||"",level:resourceContext.level||"",title:resourceContext.title||assignment?.title||""}:null;',
'  const instructions=lunaHomeworkDirectInstruction()+'+JSON.stringify('\n'+schema)+';',
'  const meta={assignment:{id:assignment?.id||null,course:assignment?.course||"",topic:assignment?.topic||"",title:assignment?.title||""},resourceContext:safeContext,manualAnswerKey:answerKey||null};',
'  const content=[{type:"input_text",text:JSON.stringify(meta)},{type:"input_text",text:"ÖĞRENCİ ÖDEV DOSYASI. Tüm sayfaları doğrudan Luna Vision ile analiz et. Beklenen fiziksel sayfa sayısı: "+(expectedStudentPages||"bilinmiyor")+"."},{type:"input_file",filename:studentFile.fileName,file_data:"data:"+studentFile.mimeType+";base64,"+studentFile.base64}];',
'  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"medium"});',
'  let parsed=normalizeHomeworkAnalysis(parseJsonText(ai.text));',
'  parsed=validateLunaDirectAnswerKey(parsed,answerKey);',
'  parsed=validateHomeworkPageCoverage(parsed,expectedStudentPages,0);',
'  parsed=validateLunaQuestionAccounting(parsed);',
'  parsed=deriveHomeworkReviewReasons(parsed);',
'  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});',
'  parsed.studentFileSource=studentFileSource;parsed.studentFileDriveUsed=!!studentFile.driveUsed;parsed.analysisArchitecture="direct_luna_vision";',
'  writeHomeworkDiagnostic(parsed,cost,assignment);',
'  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});',
'}'
];
const newHandle=lines.join('\n');
hs=hs.slice(0,start)+directInstruction+accounting+keyValidator+newHandle+hs.slice(end);
fs.writeFileSync(hp,hs,'utf8');
const ap=path.join(ROOT,analyze.file);let as=fs.readFileSync(ap,'utf8');
as=as.replace('<div class="notice"><div><b>Kaynak bağlantısı</b>${rc?.driveFileId?`Drive kaynak PDF bağlı${rc.answerKeyDriveFileId?" · Cevap anahtarı bağlı":""}${rc.questionCount?` · ${rc.questionCount} soru`:""}`:"Drive kaynak PDF bağlı değil"}</div></div>','<div class="notice"><div><b>Doğrudan Luna Vision</b>Seçtiğiniz öğrenci PDF/görseli doğrudan Luna’ya gönderilir. Bilgisayardan yüklemede Drive kontrol edilmez.</div></div>');
fs.writeFileSync(ap,as,'utf8');
const sp=path.join(ROOT,submit.file);let ss=fs.readFileSync(sp,'utf8');
ss=ss.replace('const fileData=studentFileSource==="local"?await fileToBase64(file):null,answerKey=q("answerKey").value.trim()||null,resourceContext=assignmentResourceContext(a);','const fileData=studentFileSource==="local"?await fileToBase64(file):null,answerKey=q("answerKey").value.trim()||null,rawContext=assignmentResourceContext(a),resourceContext=rawContext?{resourceId:rawContext.resourceId,course:rawContext.course,unit:rawContext.unit,topic:rawContext.topic,level:rawContext.level,title:rawContext.title}:null;');
ss=ss.replace('<div class="section"><h3>Atama Soru Kapsamı</h3><div class="cell-sub">Eşleşen soru sayısı: ${an.matchedQuestionCount||0}${an.matchedQuestionNumbers?.length?` · Basılı numaralar: ${an.matchedQuestionNumbers.join(", ")}`:""}<br>${an.assignmentMatchEvidence||"—"}</div></div>','<div class="section"><h3>Luna Analiz Mimarisi</h3><div class="cell-sub">${an.analysisArchitecture==="direct_luna_vision"?"PDF doğrudan Luna Vision tarafından analiz edildi":"—"}</div></div>');
ss=ss.replace('<div class="section"><h3>Pedagojik Özet</h3><div class="cell-sub">${an.reasoningProfile?.summary||an.summary||"—"}</div></div>','<div class="section"><h3>Pedagojik Karne</h3><div class="cell-sub"><b>Özet:</b> ${an.reasoningProfile?.summary||an.summary||"—"}<br><br><b>Güçlü yönler:</b> ${(an.reasoningProfile?.strengths||[]).join(", ")||"—"}<br><b>Tekrarlayan hatalar:</b> ${(an.reasoningProfile?.recurringErrors||[]).join(", ")||"—"}<br><b>Kavramsal eksikler:</b> ${(an.reasoningProfile?.conceptualGaps||[]).join(", ")||"—"}<br><b>İşlem/prosedür eksikleri:</b> ${(an.reasoningProfile?.proceduralGaps||[]).join(", ")||"—"}<br><b>Dikkat örüntüleri:</b> ${(an.reasoningProfile?.attentionPatterns||[]).join(", ")||"—"}<br><b>Önerilen çalışma:</b> ${(an.reasoningProfile?.recommendedActions||[]).join(", ")||"—"}</div></div>');
fs.writeFileSync(sp,ss,'utf8');
const frontend=m.frontend.map(e=>fs.readFileSync(path.join(ROOT,e.file),'utf8')).join('');
const backend=m.backend.map(e=>fs.readFileSync(path.join(ROOT,e.file),'utf8')).join('');
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend,'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.10.5\n','utf8');
console.log('v0.10.5 direct Luna Vision architecture applied');