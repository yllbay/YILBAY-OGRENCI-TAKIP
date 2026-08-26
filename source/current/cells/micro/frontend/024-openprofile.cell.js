

window.openProfile=id=>{selectedProfileStudentId=id;view="profile";profile()}
function profile(){
 if(!db.students.length){shell(`<h1>Öğrenci Profili</h1><div class="card">Önce öğrenci ekleyin.</div>`,"profile");return}
 if(!selectedProfileStudentId||!db.students.some(s=>s.id===selectedProfileStudentId))selectedProfileStudentId=db.students[0].id;
 const s=db.students.find(x=>x.id===selectedProfileStudentId);
 const rs=db.results.filter(r=>r.studentId===s.id).slice().sort((a,b)=>String(b.date).localeCompare(String(a.date)));
 const as=db.assignments.filter(a=>a.studentId===s.id).slice().sort((a,b)=>Number(b.id)-Number(a.id));
 const avg=rs.length?Math.round(rs.reduce((t,r)=>t+Number(r.score||0),0)/rs.length):0;
 const low=rs.filter(r=>r.score<db.threshold).length;
 shell(`<div class="toolbar"><h1>Öğrenci Profili</h1><select onchange="selectedProfileStudentId=Number(this.value);profile()">${db.students.map(x=>`<option value="${x.id}" ${x.id===s.id?"selected":""}>${x.name}</option>`).join("")}</select></div>
 <div class="grid">
  <div class="card"><div class="muted">Öğrenci</div><div class="kpi" style="font-size:20px">${s.name}</div><div>${s.grade}. sınıf · ${s.target||"—"}</div></div>
  <div class="card"><div class="muted">Ortalama başarı</div><div class="kpi">%${avg}</div></div>
  <div class="card"><div class="muted">Bekleyen atama</div><div class="kpi">${as.filter(a=>a.status!=="Tamamlandı").length}</div></div>
  <div class="card"><div class="muted">Tekrar sinyali</div><div class="kpi">${low}</div></div>
 </div>
 <h2>Dersler ve kaynak seviyeleri</h2><div class="list">${(s.courses||[]).map(c=>`<div class="item"><b>${c}</b> <span class="badge mid">${s.levels?.[c]||"Orta"}</span></div>`).join("")||"<div class='card'>Ders seçilmemiş.</div>"}</div>
 <h2>Son atamalar</h2><table><thead><tr><th>Tür</th><th>İçerik</th><th>Konu</th><th>Durum</th><th>Başarı</th></tr></thead><tbody>${as.slice(0,10).map(a=>`<tr><td>${a.kind}</td><td>${a.title}</td><td>${a.course} / ${a.topic}</td><td>${a.status}</td><td>${a.score!=null?`%${a.score}`:"—"}</td></tr>`).join("")||`<tr><td colspan="5">Atama yok.</td></tr>`}</tbody></table>
 <h2>Son sonuçlar</h2><table><thead><tr><th>Tarih</th><th>Tür</th><th>Ders / Konu</th><th>Başarı</th></tr></thead><tbody>${rs.slice(0,12).map(r=>`<tr><td>${r.date}</td><td>${r.kind}</td><td>${r.course} / ${r.topic}</td><td><span class="badge ${scoreClass(r.score)}">%${r.score}</span></td></tr>`).join("")||`<tr><td colspan="4">Sonuç yok.</td></tr>`}</tbody></table>`,"profile")
}

/* CELL:30-curriculum | layer:frontend | generated-from:v0.8.1 */

/* CELL:30-curriculum | layer:frontend | generated-from:v0.7.2 */
function curriculum(){
 let cards="";for(const [course,units] of Object.entries(db.curriculum)){cards+=`<div class="card"><div class="section-head"><h2 style="margin:0">${course}</h2><span class="badge info">${Object.values(units).reduce((n,x)=>n+x.length,0)} konu</span></div>`;for(const [u,topics] of Object.entries(units)){cards+=`<div class="item"><div class="cell-title">${u}</div><div style="margin-top:8px">${topics.map(t=>`<span class="badge neutral">${t}</span>`).join(" ")}</div></div>`}cards+="</div>"}
 shell(`${pageHead("Ders ve Üniteler","Ders, ünite ve alt konu yapısını yönetin.",`<button class="btn primary" onclick="currModal()">+ Müfredat Ekle</button>`)}<div class="list">${cards||emptyState("Müfredat boş","Ders ve konu ekleyerek başlayın.")}</div>`,"curriculum")
}
window.currModal=()=>modal(`<h2>Müfredat Ekle</h2><div class="formgrid"><div class="field"><label>Ders</label><input id="ccourse"></div><div class="field"><label>Ünite</label><input id="cunit"></div><div class="field"><label>Alt ünite / konu</label><input id="ctopic"></div></div><div class="modal-actions"><button class="btn primary" onclick="addCurr()">Kaydet</button></div>`)
window.addCurr=()=>{let c=q("ccourse").value.trim(),u=q("cunit").value.trim(),t=q("ctopic").value.trim();if(!c||!u||!t)return alert("Tüm alanlar gerekli");db.curriculum[c]??={};db.curriculum[c][u]??=[];if(!db.curriculum[c][u].includes(t))db.curriculum[c][u].push(t);save();closeModal();curriculum()}
function topicOptions(){let out="";for(const [c,units] of Object.entries(db.curriculum))for(const topics of Object.values(units))for(const t of topics)out+=`<option data-course="${c}" value="${c}|||${t}">${c} — ${t}</option>`;return out}

/* CELL:40-resources | layer:frontend | generated-from:v0.8.1 */

/* CELL:40-resources | layer:frontend | generated-from:v0.7.2 */
function resources(){
 const rows=db.resources.map(r=>`<tr><td><div class="cell-title">${r.title}</div><div class="cell-sub">${r.type||"PDF"}</div></td><td>${r.course}</td><td>${r.topic}</td><td><span class="badge neutral">${r.level}</span></td></tr>`).join("");
 shell(`${pageHead("Kaynak Havuzu","PDF ödev ve çalışma kaynaklarını ders, konu ve zorluk düzeyine göre yönetin.",`<button class="btn primary" onclick="resourceModal()">+ Kaynak Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Kaynak</th><th>Ders</th><th>Konu</th><th>Seviye</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Kaynak bulunamadı","İlk PDF kaynağınızı ekleyin.")}`,"resources")
}
window.resourceModal=()=>modal(`<h2>Kaynak Ekle</h2><div class="formgrid"><div class="field"><label>Başlık</label><input id="rtitle"></div><div class="field"><label>Konu</label><select id="rtopic">${topicOptions()}</select></div><div class="field"><label>Zorluk</label><select id="rlevel"><option>Başlangıç</option><option>Kolay</option><option>Orta</option><option>Orta-Zor</option><option>Zor</option><option>İleri</option></select></div><div class="field"><label>Drive bağlantısı / File ID</label><input id="rurl"></div></div><div class="modal-actions"><button class="btn primary" onclick="addResource()">Kaydet</button></div>`)
window.addResource=()=>{const [course,topic]=q("rtopic").value.split("|||");db.resources.push({id:Date.now(),type:"PDF",course,topic,level:q("rlevel").value,title:q("rtitle").value||topic+" Kaynak",url:q("rurl").value});save();closeModal();resources()}

/* CELL:50-exams | layer:frontend | generated-from:v0.8.1 */

/* CELL:50-exams | layer:frontend | generated-from:v0.7.2 */
function exams(){
 const rows=db.exams.map(e=>`<tr><td><div class="cell-title">${e.title}</div></td><td>${e.course}</td><td>${e.topic}</td><td>${e.url?`<a href="${e.url}" target="_blank">Sınavı aç</a>`:"—"}</td></tr>`).join("");
 shell(`${pageHead("Online Sınavlar","Online test ve sınav bağlantılarını konu bazında yönetin.",`<button class="btn primary" onclick="examModal()">+ Sınav Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Sınav</th><th>Ders</th><th>Konu</th><th>Bağlantı</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Online sınav yok","İlk sınav bağlantısını ekleyin.")}`,"exams")
}
window.examModal=()=>modal(`<h2>Online Sınav Ekle</h2><div class="formgrid"><div class="field"><label>Başlık</label><input id="etitle"></div><div class="field"><label>Konu</label><select id="etopic">${topicOptions()}</select></div><div class="field"><label>Link</label><input id="eurl"></div></div><div class="modal-actions"><button class="btn primary" onclick="addExam()">Kaydet</button></div>`)
window.addExam=()=>{const [course,topic]=q("etopic").value.split("|||");db.exams.push({id:Date.now(),course,topic,title:q("etitle").value||topic+" Online Test",url:q("eurl").value});save();closeModal();exams()}

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.8.1 */

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.7.2 */
function assignments(){
 const rows=db.assignments.slice().reverse().map(a=>`<tr><td><div class="cell-title">${studentName(a.studentId)}</div></td><td><span class="badge info">${a.kind}</span></td><td><div class="cell-title">${a.title}</div><div class="cell-sub">${a.course} · ${a.topic}</div></td><td><span class="badge ${a.status==="Tamamlandı"?"good":"mid"}">${a.status}</span></td><td>${a.status==="Tamamlandı"?`<span class="muted">Tamamlandı</span>`:a.status==="Öğretmen Kontrolü"?`<div class="row-actions"><button class="btn primary small" onclick="reviewHomeworkAnalysis(${a.id})">AI analizini kontrol et</button><button class="btn ghost small" onclick="analyzeAssignment(${a.id})">Yeniden tara</button></div>`:`<div class="row-actions"><button class="btn ghost small" onclick="completeAssignment(${a.id})">Manuel sonuç</button>${a.kind==="PDF Kaynak"?`<button class="btn primary small" onclick="analyzeAssignment(${a.id})">AI ile ödevi tara</button>`:""}</div>`}</td></tr>`).join("");
 shell(`${pageHead("Atamalar","Öğrencilere kaynak ve online sınav atayın, tamamlanma durumunu takip edin.",`<button class="btn primary" onclick="assignmentModal()">+ Yeni Atama</button>`)}${rows?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Tür</th><th>İçerik</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Henüz atama yok","Yeni atama oluşturarak çalışma akışını başlatın.")}`,"assignments")
}
window.assignmentModal=()=>modal(`<h2>Yeni Atama</h2><div class="formgrid">
<div class="field"><label>Öğrenci</label><select id="astudent">${db.students.map(s=>`<option value="${s.id}">${s.name}</option>`).join("")}</select></div>
<div class="field"><label>Atama türü</label><select id="akind" onchange="refreshAssignmentItems()"><option>PDF Kaynak</option><option>Online Sınav</option></select></div>
<div class="field" style="grid-column:1/-1"><label>İçerik</label><select id="aitem"></select></div>
</div><div class="modal-actions"><button class="btn primary" onclick="addAssignment()">Ata</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
window.refreshAssignmentItems=()=>{const k=q("akind").value,items=k==="PDF Kaynak"?db.resources:db.exams;q("aitem").innerHTML=items.map(x=>`<option value="${x.id}">${x.title} — ${x.course} / ${x.topic}</option>`).join("")}
window.addAssignment=()=>{const kind=q("akind").value,items=kind==="PDF Kaynak"?db.resources:db.exams,item=items.find(x=>x.id===Number(q("aitem").value));if(!item)return alert("Atanabilir içerik yok");db.assignments.push({id:Date.now(),studentId:Number(q("astudent").value),kind,title:item.title,course:item.course,topic:item.topic,sourceId:item.id,status:"Bekliyor",assignedAt:new Date().toISOString().slice(0,10)});save();closeModal();assignments()}
window.reviewHomeworkAnalysis=id=>{
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
window.completeAssignment=id=>{const a=db.assignments.find(x=>x.id===id);if(!a)return;modal(`<h2>Atamayı Tamamla</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} — ${a.course} / ${a.topic}</p><div class="field"><label>Başarı %</label><input id="ascore" type="number" min="0" max="100"></div><div class="modal-actions"><button class="btn primary" onclick="saveAssignmentResult(${id})">Kaydet</button></div>`)}
window.saveAssignmentResult=id=>{const a=db.assignments.find(x=>x.id===id);if(!a)return;const score=Math.max(0,Math.min(100,Number(q("ascore").value)));a.status="Tamamlandı";a.completedAt=new Date().toISOString().slice(0,10);a.score=score;db.results.push({id:Date.now(),studentId:a.studentId,kind:a.kind==="PDF Kaynak"?"Ödev":"Online Sınav",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});if(score<db.threshold&&!db.repeatSignals.some(r=>r.assignmentId===a.id&&r.status==="Bekliyor"))db.repeatSignals.push({id:Date.now()+1,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString()});save();closeModal();assignments()}
function results(){
 const rows=db.results.slice().reverse().map(r=>`<tr><td><div class="cell-title">${studentName(r.studentId)}</div></td><td>${r.kind}</td><td><div class="cell-title">${r.topic}</div><div class="cell-sub">${r.course}</div></td><td><span class="badge ${scoreClass(r.score)}">%${r.score}</span></td><td>${r.date}</td></tr>`).join("");
 const analyses=db.homeworkAnalyses.slice().reverse().slice(0,12).map(a=>`<tr><td>${studentName(a.studentId)}</td><td>${a.course} / ${a.topic}</td><td><span class="badge ${a.needsTeacherReview&&!a.teacherReviewed?"mid":"good"}">${a.needsTeacherReview&&!a.teacherReviewed?"Öğretmen Kontrolü":a.teacherReviewed?"Öğretmen Onaylı":"AI Kesinleştirdi"}</span></td><td>%${Math.round(Number(a.teacherScore??a.scorePercent)||0)}</td><td>%${Math.round((Number(a.confidence)||0)*100)}</td><td>${Number(a.costTry||0).toFixed(4)} TL</td></tr>`).join("");
 shell(`${pageHead("Başarı Sonuçları","Ödev ve online sınav başarılarını kaydedin. Adaptif tekrar eşiği %${db.threshold}.",`<button class="btn primary" onclick="resultModal()">+ Sonuç Gir</button>`)}${rows?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Tür</th><th>Konu</th><th>Başarı</th><th>Tarih</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Sonuç bulunamadı","İlk ödev veya sınav sonucunu girin.")}<div class="section"><div class="section-head"><h2>AI Ödev Analiz Geçmişi</h2><span class="muted">Son 12 analiz</span></div>${analyses?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Ders / Konu</th><th>Durum</th><th>Başarı</th><th>AI Güveni</th><th>Maliyet</th></tr></thead><tbody>${analyses}</tbody></table>`):emptyState("AI analiz geçmişi yok","İlk AI ödev taramasından sonra burada görünecek.")}</div>`,"results")
}
window.resultModal=()=>modal(`<h2>Sonuç Gir</h2><div class="formgrid"><div class="field"><label>Öğrenci</label><select id="xstudent">${db.students.map(s=>`<option value="${s.id}">${s.name}</option>`).join("")}</select></div><div class="field"><label>Tür</label><select id="xkind"><option>Ödev</option><option>Online Sınav</option></select></div><div class="field"><label>Konu</label><select id="xtopic">${topicOptions()}</select></div><div class="field"><label>Başarı %</label><input id="xscore" type="number" min="0" max="100"></div></div><div class="modal-actions"><button class="btn primary" onclick="addResult()">Kaydet</button></div>`)
window.addResult=()=>{const [course,topic]=q("xtopic").value.split("|||"),score=Math.max(0,Math.min(100,Number(q("xscore").value)));db.results.push({id:Date.now(),studentId:Number(q("xstudent").value),kind:q("xkind").value,course,topic,score,date:new Date().toISOString().slice(0,10)});save();closeModal();results()}

/* CELL:70-planner | layer:frontend | generated-from:v0.8.1 */

/* CELL:70-planner | layer:frontend | generated-from:v0.7.2 */
let selectedStudentId=null;
