from pathlib import Path
import re

root=Path('/tmp/yilbay071')
server=root/'app/server.js'
appjs=root/'app/public/app.js'
version=root/'VERSION'

s=server.read_text(encoding='utf-8')
s=s.replace('version:"0.7.0"','version:"0.7.1"')

# Harden homework-analysis output: normalize numeric fields and require teacher review for low-confidence scans.
anchor='async function handleHomework(req,res){'
helper=r'''function normalizeHomeworkAnalysis(x={}){
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
'''
if anchor not in s: raise SystemExit('handleHomework anchor missing')
s=s.replace(anchor,helper+anchor,1)

# Strengthen homework instructions/schema and normalize before returning.
s=s.replace('Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.',
'''Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.
Kesin göremediğin işaret veya çözüm için tahmin yürütme. Soruların/işaretlerin yeterli kısmı okunamıyorsa needsTeacherReview=true yap.
confidence 0 ile 1 arasında olmalı. confidence 0.65 altındaysa sonuç öğretmen onayı gerektirmelidir.''')

old='''  const parsed=parseJsonText(ai.text);\n  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});\n  return json(res,200,{ok:true,analysis:parsed,usage:ai.data?.usage||null,cost});'''
new='''  const parsed=normalizeHomeworkAnalysis(parseJsonText(ai.text));\n  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});\n  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});'''
if old not in s: raise SystemExit('homework return block missing')
s=s.replace(old,new,1)
server.write_text(s,encoding='utf-8')

j=appjs.read_text(encoding='utf-8')
j=j.replace('<span class="version">v0.7.0</span>','<span class="version">v0.7.1</span>')

# Guarantee migrated data collections.
needle=''' x.videoSuggestions??={};\n x.threshold??=70;'''
replacement=''' x.videoSuggestions??={};\n x.homeworkAnalyses??=[];\n x.repeatSignals??=[];\n x.threshold??=70;'''
if needle not in j: raise SystemExit('normalizeDb anchor missing')
j=j.replace(needle,replacement,1)

# Manual results should also create a repeat signal when below threshold.
old='''window.saveAssignmentResult=id=>{const a=db.assignments.find(x=>x.id===id);if(!a)return;const score=Math.max(0,Math.min(100,Number(q("ascore").value)));a.status="Tamamlandı";a.completedAt=new Date().toISOString().slice(0,10);a.score=score;db.results.push({id:Date.now(),studentId:a.studentId,kind:a.kind==="PDF Kaynak"?"Ödev":"Online Sınav",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});save();closeModal();assignments()}'''
new='''window.saveAssignmentResult=id=>{const a=db.assignments.find(x=>x.id===id);if(!a)return;const score=Math.max(0,Math.min(100,Number(q("ascore").value)));a.status="Tamamlandı";a.completedAt=new Date().toISOString().slice(0,10);a.score=score;db.results.push({id:Date.now(),studentId:a.studentId,kind:a.kind==="PDF Kaynak"?"Ödev":"Online Sınav",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});if(score<db.threshold&&!db.repeatSignals.some(r=>r.assignmentId===a.id&&r.status==="Bekliyor"))db.repeatSignals.push({id:Date.now()+1,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString()});save();closeModal();assignments()}'''
if old not in j: raise SystemExit('manual result block missing')
j=j.replace(old,new,1)

# Replace homework submit flow with confidence gate, repeat signal, safe metadata and visible cost.
pat=r'window\.submitHomeworkAnalysis=async id=>\{.*?\n\}'
m=re.search(pat,j,flags=re.S)
if not m: raise SystemExit('submitHomeworkAnalysis function missing')
new_submit=r'''window.submitHomeworkAnalysis=async id=>{
 const a=db.assignments.find(x=>x.id===id),file=q("homeworkFile")?.files?.[0];if(!a||!file)return alert("Ödev dosyasını seçin");
 if(file.size>14*1024*1024)return alert("Bu sürümde dosya en fazla 14 MB olabilir.");
 const btn=document.querySelector(".modal-actions .btn.primary");if(btn){btn.disabled=true;btn.textContent="AI tarıyor…"}
 try{
  const fileData=await fileToBase64(file),answerKey=q("answerKey").value.trim()||null;
  const data=await apiJson("/api/ai/analyze-homework",{fileData,mimeType:file.type||"application/pdf",fileName:file.name,assignment:{id:a.id,studentId:a.studentId,course:a.course,topic:a.topic,title:a.title},answerKey});
  const an=data.analysis||{},score=Math.round(Number(an.scorePercent)||0),reviewRequired=!!an.needsTeacherReview||data.autoFinalize===false;
  db.homeworkAnalyses.push({id:Date.now(),assignmentId:a.id,studentId:a.studentId,course:a.course,topic:a.topic,date:new Date().toISOString().slice(0,10),fileName:file.name,fileSize:file.size,mimeType:file.type||"application/pdf",costTry:Number(data.cost?.try||0),...an});
  a.completedAt=new Date().toISOString().slice(0,10);a.score=score;a.aiConfidence=Number(an.confidence||0);
  if(reviewRequired){
    a.status="Öğretmen Kontrolü";
  }else{
    a.status="Tamamlandı";
    db.results.push({id:Date.now()+1,studentId:a.studentId,kind:"AI Ödev Analizi",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});
    if(score<db.threshold&&!db.repeatSignals.some(r=>r.assignmentId===a.id&&r.status==="Bekliyor"))db.repeatSignals.push({id:Date.now()+2,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString()});
  }
  save();
  q("modalbg").querySelector(".modal").innerHTML=`<h2>${reviewRequired?"Öğretmen Kontrolü Gerekli":"Ödev Analizi Tamamlandı"}</h2><div class="result-hero"><div class="kpi">%${score}</div><div><div class="cell-title">${an.correct||0} doğru · ${an.wrong||0} yanlış · ${an.blank||0} boş</div><div class="cell-sub">Güven: %${Math.round((Number(an.confidence)||0)*100)}${data.cost?` · AI maliyeti ${Number(data.cost.try||0).toFixed(4)} TL`:""}</div></div></div>
   ${reviewRequired?`<div class="notice error"><div><b>Otomatik sonuç kesinleştirilmedi</b>AI güveni yeterli olmadığı için bu analiz başarı sonuçlarına ve tekrar motoruna otomatik aktarılmadı. Atamalar ekranından “Manuel sonuç” ile öğretmen onayı verin.</div></div>`:`<div class="notice"><div><b>${score<db.threshold?"Tekrar sinyali oluşturuldu":"Başarı yeterli"}</b>${score<db.threshold?`%${db.threshold} eşiğinin altında olduğu için ${a.topic} konusu sonraki programda tekrar önceliği alacak.`:"Konu için otomatik tekrar sinyali oluşturulmadı."}</div></div>`}
   <div class="section"><h3>Zayıf Alanlar</h3>${(an.weaknesses||[]).map(x=>`<span class="course-chip">${x}</span>`).join("")||"—"}</div>
   <div class="section"><h3>Hata Türleri</h3>${(an.errorTypes||[]).map(x=>`<span class="course-chip">${typeof x==="string"?x:(x.type||x.label||JSON.stringify(x))}</span>`).join("")||"—"}</div>
   <div class="modal-actions"><button class="btn primary" onclick="closeModal();assignments()">Tamam</button></div>`;
 }catch(e){alert("Ödev analizi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent="Dosyayı Tara"}}
}'''
j=j[:m.start()]+new_submit+j[m.end():]

appjs.write_text(j,encoding='utf-8')
version.write_text('0.7.1\n',encoding='utf-8')
print('patched v0.7.1')
