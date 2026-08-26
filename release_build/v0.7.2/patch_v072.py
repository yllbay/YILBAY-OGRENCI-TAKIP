from pathlib import Path

root=Path('/tmp/yilbay072')
app=root/'app/public/app.js'
server=root/'app/server.js'
version=root/'VERSION'
readme=root/'README.md'

s=app.read_text(encoding='utf-8')
s=s.replace('v0.7.1','v0.7.2')

old='''<td>${a.status==="Tamamlandı"?`<span class="muted">Tamamlandı</span>`:`<div class="row-actions"><button class="btn ghost small" onclick="completeAssignment(${a.id})">Manuel sonuç</button>${a.kind==="PDF Kaynak"?`<button class="btn primary small" onclick="analyzeAssignment(${a.id})">AI ile ödevi tara</button>`:""}</div>`}</td>'''
new='''<td>${a.status==="Tamamlandı"?`<span class="muted">Tamamlandı</span>`:a.status==="Öğretmen Kontrolü"?`<div class="row-actions"><button class="btn primary small" onclick="reviewHomeworkAnalysis(${a.id})">AI analizini kontrol et</button><button class="btn ghost small" onclick="analyzeAssignment(${a.id})">Yeniden tara</button></div>`:`<div class="row-actions"><button class="btn ghost small" onclick="completeAssignment(${a.id})">Manuel sonuç</button>${a.kind==="PDF Kaynak"?`<button class="btn primary small" onclick="analyzeAssignment(${a.id})">AI ile ödevi tara</button>`:""}</div>`}</td>'''
if old not in s: raise SystemExit('assignment action anchor not found')
s=s.replace(old,new,1)

anchor='''window.completeAssignment=id=>{const a=db.assignments.find(x=>x.id===id);if(!a)return;modal(`<h2>Atamayı Tamamla</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} — ${a.course} / ${a.topic}</p><div class="field"><label>Başarı %</label><input id="ascore" type="number" min="0" max="100"></div><div class="modal-actions"><button class="btn primary" onclick="saveAssignmentResult(${id})">Kaydet</button></div>`)}\n'''
review=r'''window.reviewHomeworkAnalysis=id=>{
 const a=db.assignments.find(x=>x.id===id);if(!a)return;
 const an=db.homeworkAnalyses.filter(x=>x.assignmentId===id).slice().sort((x,y)=>Number(y.id)-Number(x.id))[0];
 if(!an)return alert("Bu atama için AI analiz kaydı bulunamadı.");
 modal(`<h2>AI Analizini Öğretmen Kontrolü</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} · ${a.course} / ${a.topic}</p>
 <div class="result-hero"><div class="kpi">%${Math.round(Number(an.scorePercent)||0)}</div><div><div class="cell-title">${an.correct||0} doğru · ${an.wrong||0} yanlış · ${an.blank||0} boş</div><div class="cell-sub">AI güveni: %${Math.round((Number(an.confidence)||0)*100)} · ${an.fileName||"Dosya"}</div></div></div>
 <div class="section"><h3>AI zayıf alanları</h3>${(an.weaknesses||[]).map(x=>`<span class="course-chip">${x}</span>`).join("")||"—"}</div>
 <div class="field"><label>Öğretmen tarafından onaylanan başarı %</label><input id="teacherScore" type="number" min="0" max="100" value="${Math.round(Number(an.scorePercent)||0)}"></div>
 <div class="field"><label>Öğretmen notu</label><textarea id="teacherReviewNote" rows="3" placeholder="Opsiyonel kontrol notu"></textarea></div>
 <div class="modal-actions"><button class="btn primary" onclick="approveHomeworkAnalysis(${id},${an.id})">Onayla ve Sonucu İşle</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
}
window.approveHomeworkAnalysis=(assignmentId,analysisId)=>{
 const a=db.assignments.find(x=>x.id===assignmentId),an=db.homeworkAnalyses.find(x=>x.id===analysisId);if(!a||!an)return;
 const score=Math.max(0,Math.min(100,Number(q("teacherScore").value)));
 an.teacherReviewed=true;an.teacherReviewedAt=new Date().toISOString();an.teacherScore=score;an.teacherNote=q("teacherReviewNote").value.trim();
 a.status="Tamamlandı";a.completedAt=new Date().toISOString().slice(0,10);a.score=score;a.teacherReviewed=true;
 const existing=db.results.find(r=>r.assignmentId===a.id);
 if(existing){existing.score=score;existing.kind="AI Ödev Analizi · Öğretmen Onaylı";existing.date=a.completedAt}
 else db.results.push({id:Date.now(),studentId:a.studentId,kind:"AI Ödev Analizi · Öğretmen Onaylı",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});
 db.repeatSignals=db.repeatSignals.filter(r=>r.assignmentId!==a.id||r.status!=="Bekliyor");
 if(score<db.threshold)db.repeatSignals.push({id:Date.now()+1,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString(),source:"teacher-review"});
 save();closeModal();assignments();
}
'''
if anchor not in s: raise SystemExit('complete assignment anchor not found')
s=s.replace(anchor,review+anchor,1)

old_results='''function results(){\n const rows=db.results.slice().reverse().map(r=>`<tr><td><div class="cell-title">${studentName(r.studentId)}</div></td><td>${r.kind}</td><td><div class="cell-title">${r.topic}</div><div class="cell-sub">${r.course}</div></td><td><span class="badge ${scoreClass(r.score)}">%${r.score}</span></td><td>${r.date}</td></tr>`).join("");\n shell(`${pageHead("Başarı Sonuçları","Ödev ve online sınav başarılarını kaydedin. Adaptif tekrar eşiği %${db.threshold}.",`<button class="btn primary" onclick="resultModal()">+ Sonuç Gir</button>`)}${rows?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Tür</th><th>Konu</th><th>Başarı</th><th>Tarih</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Sonuç bulunamadı","İlk ödev veya sınav sonucunu girin.")}`,"results")\n}\n'''
new_results='''function results(){\n const rows=db.results.slice().reverse().map(r=>`<tr><td><div class="cell-title">${studentName(r.studentId)}</div></td><td>${r.kind}</td><td><div class="cell-title">${r.topic}</div><div class="cell-sub">${r.course}</div></td><td><span class="badge ${scoreClass(r.score)}">%${r.score}</span></td><td>${r.date}</td></tr>`).join("");\n const analyses=db.homeworkAnalyses.slice().reverse().slice(0,12).map(a=>`<tr><td>${studentName(a.studentId)}</td><td>${a.course} / ${a.topic}</td><td><span class="badge ${a.needsTeacherReview&&!a.teacherReviewed?"mid":"good"}">${a.needsTeacherReview&&!a.teacherReviewed?"Öğretmen Kontrolü":a.teacherReviewed?"Öğretmen Onaylı":"AI Kesinleştirdi"}</span></td><td>%${Math.round(Number(a.teacherScore??a.scorePercent)||0)}</td><td>%${Math.round((Number(a.confidence)||0)*100)}</td><td>${Number(a.costTry||0).toFixed(4)} TL</td></tr>`).join("");\n shell(`${pageHead("Başarı Sonuçları","Ödev ve online sınav başarılarını kaydedin. Adaptif tekrar eşiği %${db.threshold}.",`<button class="btn primary" onclick="resultModal()">+ Sonuç Gir</button>`)}${rows?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Tür</th><th>Konu</th><th>Başarı</th><th>Tarih</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Sonuç bulunamadı","İlk ödev veya sınav sonucunu girin.")}<div class="section"><div class="section-head"><h2>AI Ödev Analiz Geçmişi</h2><span class="muted">Son 12 analiz</span></div>${analyses?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Ders / Konu</th><th>Durum</th><th>Başarı</th><th>AI Güveni</th><th>Maliyet</th></tr></thead><tbody>${analyses}</tbody></table>`):emptyState("AI analiz geçmişi yok","İlk AI ödev taramasından sonra burada görünecek.")}</div>`,"results")\n}\n'''
if old_results not in s: raise SystemExit('results anchor not found')
s=s.replace(old_results,new_results,1)

app.write_text(s,encoding='utf-8')
ss=server.read_text(encoding='utf-8').replace('"0.7.1"','"0.7.2"').replace('READY 0.7.1','READY 0.7.2')
server.write_text(ss,encoding='utf-8')
version.write_text('0.7.2\n',encoding='utf-8')
readme.write_text('# YILBAY Öğrenci Takip — v0.7.2\n\n- AI ödev analiz geçmişi\n- Düşük güvenli analizler için öğretmen kontrol/onay akışı\n- Öğretmen onayı sonrası başarı sonucu ve tekrar sinyali\n- Analiz güven/maliyet görünürlüğü\n',encoding='utf-8')
print('patched v0.7.2')
