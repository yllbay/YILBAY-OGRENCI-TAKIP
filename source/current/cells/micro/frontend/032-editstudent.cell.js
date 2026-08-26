window.editStudent=id=>{const s=db.students.find(x=>x.id===id);if(!s)return;modal(`<h2>Öğrenci Düzenle</h2><input type="hidden" id="sid" value="${id}"><div class="formgrid">
<div class="field"><label>Ad Soyad</label><input id="sname" value="${s.name}"></div>
<div class="field"><label>Sınıf</label><input id="sgrade" value="${s.grade||""}"></div>
<div class="field"><label>Hedef</label><input id="starget" value="${s.target||""}"></div>
<div class="field"><label>Kayıt Tarihi</label><input id="sregistered" type="date" value="${s.registeredAt||""}"></div>
<div class="field"><label>Kurs Bitiş Tarihi</label><input id="senddate" type="date" value="${s.courseEndDate||""}"></div>
<div class="field"><label>Haftalık Çalışma Günü</label><input id="sstudydays" type="number" min="1" max="7" value="${s.weeklyStudyDays||6}"></div>
<div class="field"><label>Günlük Çalışma Süresi (dk)</label><input id="sdailyminutes" type="number" min="30" max="600" step="15" value="${s.dailyMinutes||120}"></div>
<div class="field"><label>AI Otomatik Planlama</label><select id="saiauto"><option value="true" ${s.aiAutoPlan!==false?"selected":""}>Açık</option><option value="false" ${s.aiAutoPlan===false?"selected":""}>Kapalı</option></select></div>
</div><h3>Dersler / seviyeler</h3><div class="list">${courseLevelFields(s.courses||[],s.levels||{})}</div><div class="modal-actions"><button class="btn primary" onclick="saveStudentEdit()">Kaydet</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>`)}
