import fs from 'fs';
import path from 'path';
const ROOT='/tmp/yilbay098';
const manifestPath=path.join(ROOT,'cells','micro-cell-manifest.json');
const m=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
if(m.version!=='0.9.7'||m.protocol!=='micro-cell-v2-ast')throw new Error('Expected verified v0.9.7 source');
for(const e of [...m.frontend,...m.backend]){const p=path.join(ROOT,e.file);let s=fs.readFileSync(p,'utf8');s=s.replaceAll('0.9.7','0.9.8');fs.writeFileSync(p,s,'utf8')}

const hwEntry=m.backend.find(x=>x.name==='handleHomework');
if(!hwEntry)throw new Error('handleHomework missing');
const searchRel='cells/micro/backend/032a-homeworkanswerkeysearchinstruction.cell.js';
const evidenceRel='cells/micro/backend/032b-validatehomeworkanswerkeyevidence.cell.js';
const searchSrc=`function homeworkAnswerKeySearchInstruction(){return \`CEVAP ANAHTARI ARAMA PROTOKOLÜ:\nÖnce manuel veya ayrı cevap anahtarı verilmişse onu kesin referans kabul et. Ayrı anahtar yoksa KAYNAK PDF'nin tamamında cevap anahtarı ara. Cevap anahtarı testin bulunduğu aynı sayfanın üstünde veya altında, bir sonraki sayfanın üstünde veya altında, PDF'nin son sayfalarında ya da son sayfalarda test isimleriyle toplu tabloda olabilir. Toplu cevap anahtarında assignment.title, resourceContext.title, course ve topic bilgilerini kullanarak doğru test bloğunu eşleştir. Öğrencinin kendi işaretlerini asla cevap anahtarı sayma. Birden fazla blok aynı derecede olasıysa answerKeySource=\\\"ambiguous\\\" yap. Hiç güvenilir anahtar yoksa answerKeySource=\\\"none\\\" yap. Gömülü anahtar bulunduğunda source yalnız embedded_same_page, embedded_adjacent_page veya embedded_end_pages olabilir. answerKeyConfidence cevap anahtarının gerçekten ilgili teste ait olma güvenidir.\`}`+'\n';
const evidenceSrc=`function validateHomeworkAnswerKeyEvidence(analysis,manualAnswerKey,resourceContext){const manual=String(manualAnswerKey||'').trim(),external=String(resourceContext?.answerKeyDriveFileId||'').trim();if(manual)return {...analysis,answerKeyFound:true,answerKeySource:'manual',answerKeyConfidence:1,answerKeyEvidence:analysis.answerKeyEvidence||'Öğretmen tarafından manuel cevap anahtarı sağlandı'};if(external)return {...analysis,answerKeyFound:true,answerKeySource:'external_drive',answerKeyConfidence:1,answerKeyEvidence:analysis.answerKeyEvidence||'Ayrı Drive cevap anahtarı sağlandı'};const allowed=['embedded_same_page','embedded_adjacent_page','embedded_end_pages'],source=String(analysis.answerKeySource||'none'),confidence=Math.max(0,Math.min(1,Number(analysis.answerKeyConfidence)||0)),found=analysis.answerKeyFound===true&&allowed.includes(source),review=!found||confidence<0.75;return {...analysis,answerKeyFound:found,answerKeySource:found?source:(source==='ambiguous'?'ambiguous':'none'),answerKeyConfidence:Math.round(confidence*1000)/1000,answerKeyEvidence:String(analysis.answerKeyEvidence||'').slice(0,500),needsTeacherReview:!!analysis.needsTeacherReview||review,autoFinalize:!!analysis.autoFinalize&&!review}}\n`;
fs.writeFileSync(path.join(ROOT,searchRel),searchSrc,'utf8');
fs.writeFileSync(path.join(ROOT,evidenceRel),evidenceSrc,'utf8');

const hwPath=path.join(ROOT,hwEntry.file);let hw=fs.readFileSync(hwPath,'utf8');
hw=hw.replace('  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun.', '  const answerKeySearch=homeworkAnswerKeySearchInstruction();\n  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun.');
hw=hw.replace('Eğer cevap anahtarı sağlandıysa onu kesin referans olarak kullan. Cevap anahtarı yoksa yalnızca güvenle değerlendirebildiklerini puanla ve confidence değerini düşür.', '${answerKeySearch}\nCevap anahtarı kanıtı olmadan doğru/yanlış durumunu kesinmiş gibi uydurma.');
hw=hw.replace('"summary":"..."}`;', '"summary":"...","answerKeyFound":boolean,"answerKeySource":"manual|external_drive|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none","answerKeyConfidence":number,"answerKeyEvidence":"kısa konum/eşleşme açıklaması","answerKeyTestName":"string|null"}`;');
hw=hw.replace('const parsed=validateHomeworkQuestionCount(normalizeHomeworkAnalysis(parseJsonText(ai.text)),resourceContext?.questionCount);','const parsed=validateHomeworkAnswerKeyEvidence(validateHomeworkQuestionCount(normalizeHomeworkAnalysis(parseJsonText(ai.text)),resourceContext?.questionCount),answerKey,resourceContext);');
if(!hw.includes('homeworkAnswerKeySearchInstruction()')||!hw.includes('validateHomeworkAnswerKeyEvidence(')||!hw.includes('embedded_adjacent_page'))throw new Error('handleHomework embedded-key patch failed');
fs.writeFileSync(hwPath,hw,'utf8');

const submitEntry=m.frontend.find(x=>x.name==='submitHomeworkAnalysis');
if(!submitEntry)throw new Error('submitHomeworkAnalysis missing');
const labelRel='cells/micro/frontend/076a-homeworkanswerkeysourcelabel.cell.js';
const labelSrc=`function homeworkAnswerKeySourceLabel(source){const labels={manual:'Manuel',external_drive:'Ayrı Drive PDF',embedded_same_page:'Kaynak PDF · aynı sayfa',embedded_adjacent_page:'Kaynak PDF · sonraki sayfa',embedded_end_pages:'Kaynak PDF · son sayfalar',ambiguous:'Belirsiz',none:'Bulunamadı'};return labels[String(source||'none')]||String(source||'Bulunamadı')}\n`;
fs.writeFileSync(path.join(ROOT,labelRel),labelSrc,'utf8');
const submitPath=path.join(ROOT,submitEntry.file);let submit=fs.readFileSync(submitPath,'utf8');
submit=submit.replace('Güven: %${Math.round((Number(an.confidence)||0)*100)}${data.cost?', 'Güven: %${Math.round((Number(an.confidence)||0)*100)} · Cevap anahtarı: ${homeworkAnswerKeySourceLabel(an.answerKeySource)} (%${Math.round((Number(an.answerKeyConfidence)||0)*100)})${data.cost?');
submit=submit.replace('<div class="section"><h3>Zayıf Alanlar</h3>', '<div class="section"><h3>Cevap Anahtarı Kanıtı</h3><div class="cell-sub">${an.answerKeyEvidence||"—"}</div></div>\n   <div class="section"><h3>Zayıf Alanlar</h3>');
if(!submit.includes('homeworkAnswerKeySourceLabel(an.answerKeySource)')||!submit.includes('Cevap Anahtarı Kanıtı'))throw new Error('homework result UI patch failed');
fs.writeFileSync(submitPath,submit,'utf8');

const frontend=[];for(const e of m.frontend){if(e.name==='submitHomeworkAnalysis')frontend.push(labelSrc);frontend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
const backend=[];for(const e of m.backend){if(e.name==='handleHomework'){backend.push(searchSrc);backend.push(evidenceSrc)}backend.push(fs.readFileSync(path.join(ROOT,e.file),'utf8'))}
fs.writeFileSync(path.join(ROOT,'app','public','app.js'),frontend.join(''),'utf8');
fs.writeFileSync(path.join(ROOT,'app','server.js'),backend.join(''),'utf8');
fs.writeFileSync(path.join(ROOT,'app','VERSION'),'0.9.8\n','utf8');
console.log('v0.9.8 embedded answer-key evidence patch applied');
