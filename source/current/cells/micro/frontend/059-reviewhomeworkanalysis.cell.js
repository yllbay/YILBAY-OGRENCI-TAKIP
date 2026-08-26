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
