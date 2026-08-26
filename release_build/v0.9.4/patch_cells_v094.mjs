import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay094';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.3'||m.protocol!=='micro-cell-v2-ast')throw new Error('Expected verified v0.9.3 source');
for(const e of [...m.frontend,...m.backend]){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.3','0.9.4');fs.writeFileSync(p,s,'utf8')}

// FRONTEND: assignment -> resource context.
const submitEntry=m.frontend.find(x=>x.name==='submitHomeworkAnalysis');
const analyzeEntry=m.frontend.find(x=>x.name==='analyzeAssignment');
if(!submitEntry||!analyzeEntry)throw new Error('homework frontend cells missing');
const ctxRel='cells/micro/frontend/076a-assignmentresourcecontext.cell.js';
const ctxSrc=`function assignmentResourceContext(a){if(!a||a.kind!=='PDF Kaynak')return null;const r=db.resources.find(x=>x.id===a.sourceId);if(!r)return null;return {resourceId:r.id,driveFileId:r.driveFileId||null,answerKeyDriveFileId:r.answerKeyDriveFileId||null,questionCount:Number(r.questionCount)||null,course:r.course||a.course,unit:r.unit||'',topic:r.subtopic||r.topic||a.topic,level:r.level||'',title:r.title||a.title}}\n`;
fs.writeFileSync(path.join(ROOT,ctxRel),ctxSrc,'utf8');
const submitPath=path.join(ROOT,submitEntry.file);let submit=fs.readFileSync(submitPath,'utf8');
submit=submit.replace('const fileData=await fileToBase64(file),answerKey=q("answerKey").value.trim()||null;','const fileData=await fileToBase64(file),answerKey=q("answerKey").value.trim()||null,resourceContext=assignmentResourceContext(a);');
submit=submit.replace('assignment:{id:a.id,studentId:a.studentId,course:a.course,topic:a.topic,title:a.title},answerKey});','assignment:{id:a.id,studentId:a.studentId,course:a.course,topic:a.topic,title:a.title},answerKey,resourceContext});');
if(!submit.includes('resourceContext=assignmentResourceContext(a)')||!submit.includes('answerKey,resourceContext'))throw new Error('submit homework context patch failed');
fs.writeFileSync(submitPath,submit,'utf8');
const analyzePath=path.join(ROOT,analyzeEntry.file);let analyze=fs.readFileSync(analyzePath,'utf8');
analyze=analyze.replace('const a=db.assignments.find(x=>x.id===id);if(!a)return;','const a=db.assignments.find(x=>x.id===id);if(!a)return;const rc=assignmentResourceContext(a);');
analyze=analyze.replace('<div class="notice"><div><b>Analiz kapsamı</b>AI;', '<div class="notice"><div><b>Kaynak bağlantısı</b>${rc?.driveFileId?`Drive kaynak PDF bağlı${rc.answerKeyDriveFileId?" · Cevap anahtarı bağlı":""}${rc.questionCount?` · ${rc.questionCount} soru`:""}`:"Drive kaynak PDF bağlı değil"}</div></div>\n <div class="notice"><div><b>Analiz kapsamı</b>AI;');
fs.writeFileSync(analyzePath,analyze,'utf8');

// BACKEND: Drive download + question-count consistency.
const hwEntry=m.backend.find(x=>x.name==='handleHomework');
if(!hwEntry)throw new Error('handleHomework missing');
const dlRel='cells/micro/backend/031a-drivedownloadanalysisfile.cell.js';
const dlSrc=`async function driveDownloadAnalysisFile(fileId){if(!fileId)return null;const token=await driveRefreshAccessToken();const u='https://www.googleapis.com/drive/v3/files/'+encodeURIComponent(fileId)+'?alt=media';const r=await fetch(u,{headers:{Authorization:'Bearer '+token}});if(!r.ok){let j={};try{j=await r.json()}catch{}throw new Error(j.error?.message||('Drive dosyası indirilemedi HTTP '+r.status))}const b=Buffer.from(await r.arrayBuffer());if(b.length>14*1024*1024)throw new Error('Drive analiz dosyası 14 MB sınırını aşıyor');return {base64:b.toString('base64'),mimeType:r.headers.get('content-type')||'application/pdf',size:b.length}}\n`;
const qcRel='cells/micro/backend/031b-validatehomeworkquestioncount.cell.js';
const qcSrc=`function validateHomeworkQuestionCount(analysis,expected){const n=Math.max(0,Math.round(Number(expected)||0));if(!n)return analysis;if(Number(analysis.totalQuestions)!==n)return {...analysis,needsTeacherReview:true,autoFinalize:false,questionCountMismatch:true,expectedQuestionCount:n};return {...analysis,expectedQuestionCount:n,questionCountMismatch:false}}\n`;
fs.writeFileSync(path.join(ROOT,dlRel),dlSrc,'utf8');fs.writeFileSync(path.join(ROOT,qcRel),qcSrc,'utf8');
const hwPath=path.join(ROOT,hwEntry.file);let hw=fs.readFileSync(hwPath,'utf8');
hw=hw.replace('const {fileData,mimeType="application/pdf",fileName="odev.pdf",assignment,answerKey=null}=body;','const {fileData,mimeType="application/pdf",fileName="odev.pdf",assignment,answerKey=null,resourceContext=null}=body;');
hw=hw.replace('const content=[\n    {type:"input_text",text:JSON.stringify({assignment,answerKey})},\n    {type:"input_file",filename:fileName,file_data:`data:${mimeType};base64,${fileData}`}\n  ];',`const content=[{type:"input_text",text:JSON.stringify({assignment,answerKey,resourceContext})}];\n  if(resourceContext?.driveFileId){const src=await driveDownloadAnalysisFile(resourceContext.driveFileId);content.push({type:"input_text",text:"KAYNAK PDF - öğrencinin çözdüğü asıl soru dokümanı"},{type:"input_file",filename:"kaynak.pdf",file_data:\`data:\${src.mimeType};base64,\${src.base64}\`})}\n  if(resourceContext?.answerKeyDriveFileId){const key=await driveDownloadAnalysisFile(resourceContext.answerKeyDriveFileId);content.push({type:"input_text",text:"CEVAP ANAHTARI - kesin referans olarak kullan"},{type:"input_file",filename:"cevap_anahtari.pdf",file_data:\`data:\${key.mimeType};base64,\${key.base64}\`})}\n  content.push({type:"input_text",text:"ÖĞRENCİ ÇÖZÜM DOSYASI - değerlendirilecek çalışma"},{type:"input_file",filename:fileName,file_data:\`data:\${mimeType};base64,\${fileData}\`});`);
hw=hw.replace('const parsed=normalizeHomeworkAnalysis(parseJsonText(ai.text));','const parsed=validateHomeworkQuestionCount(normalizeHomeworkAnalysis(parseJsonText(ai.text)),resourceContext?.questionCount);');
if(!hw.includes('driveDownloadAnalysisFile(resourceContext.driveFileId)')||!hw.includes('validateHomeworkQuestionCount('))throw new Error('handleHomework Drive context patch failed');
fs.writeFileSync(hwPath,hw,'utf8');

// BOOTSTRAP template: browser fullscreen, version 2.1.0.
const boot=path.join(ROOT,'app','bootstrap','orchestrator_node.js');let bs=fs.readFileSync(boot,'utf8');
bs=bs.replaceAll('2.0.0-node','2.1.0-node').replaceAll('Node bootstrap v2.0.0','Node bootstrap v2.1.0');
bs=bs.replace('const b=cp.spawn(browser,[`--app=http://127.0.0.1:${port}`,`--user-data-dir=${path.join(RUNTIME,"browser_profile")}`]', 'const b=cp.spawn(browser,[`--app=http://127.0.0.1:${port}`,"--start-fullscreen","--start-maximized",`--user-data-dir=${path.join(RUNTIME,"browser_profile")}`]');
if(!bs.includes('--start-fullscreen'))throw new Error('bootstrap fullscreen patch failed');fs.writeFileSync(boot,bs,'utf8');

// BACKEND: safely sync launcher preferences to permanent package root on Windows.
const launchRel='cells/micro/backend/043a-installlaunchpreferences.cell.js';
const launchSrc=`function installLaunchPreferences(){if(process.platform!=='win32')return {skipped:true};const src=path.join(__dirname,'bootstrap','orchestrator_node.js'),dstDir=path.join(root,'bootstrap'),dst=path.join(dstDir,'orchestrator_node.js');fs.mkdirSync(dstDir,{recursive:true});if(fs.existsSync(src))fs.copyFileSync(src,dst);const bat='@echo off\\r\\nsetlocal\\r\\ncd /d "%~dp0"\\r\\nstart "YILBAY" /MAX powershell.exe -NoLogo -NoProfile -Command "& node \'%~dp0bootstrap\\\\orchestrator_node.js\'"\\r\\nexit /b 0\\r\\n';fs.writeFileSync(path.join(root,'PROGRAMI_CALISTIR.bat'),bat,'utf8');return {installed:true}}\n`;
const callRel='cells/micro/backend/043b-installlaunchpreferences-call.cell.js';
const callSrc=`installLaunchPreferences()\n`;
fs.writeFileSync(path.join(ROOT,launchRel),launchSrc,'utf8');fs.writeFileSync(path.join(ROOT,callRel),callSrc,'utf8');

// Rebuild runtime bundles from related cells + new cells, preserving order.
const frontend=[];for(const e of m.frontend){if(e.name==='submitHomeworkAnalysis')frontend.push(fs.readFileSync(path.join(ROOT,ctxRel),'utf8'));frontend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
const backend=[];for(const e of m.backend){if(e.name==='handleHomework'){backend.push(fs.readFileSync(path.join(ROOT,dlRel),'utf8'));backend.push(fs.readFileSync(path.join(ROOT,qcRel),'utf8'))}if(e.name==='server-listen-43'){backend.push(fs.readFileSync(path.join(ROOT,launchRel),'utf8'));backend.push(fs.readFileSync(path.join(ROOT,callRel),'utf8'))}backend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend.join(''),'utf8');fs.writeFileSync(path.join(ROOT,'app','server.js'),backend.join(''),'utf8');fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.4\n','utf8');
console.log('v0.9.4 patch applied');
