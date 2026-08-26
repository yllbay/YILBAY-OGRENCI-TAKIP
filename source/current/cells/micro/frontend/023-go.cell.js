

window.go=k=>{view=k;render()}
function render(){({dashboard,students,profile,curriculum,resources,exams,assignments,results,program,integrations}[view]||dashboard)()}

/* CELL:10-dashboard | layer:frontend | generated-from:v0.8.1 */

/* CELL:10-dashboard | layer:frontend | generated-from:v0.7.2 */
function dashboard(){
 const low=db.results.filter(r=>r.score<db.threshold), pending=db.assignments.filter(a=>a.status!=="Tamamlandı");
 const avg=db.results.length?Math.round(db.results.reduce((n,r)=>n+r.score,0)/db.results.length):0;
 shell(`${pageHead("Genel Bakış","Öğrenciler, atamalar ve akademik performansın güncel özeti.")}
 <div class="grid">
 <div class="card kpi-card"><div class="kpi-label">Aktif öğrenci</div><div class="kpi">${db.students.length}</div><div class="kpi-foot">Koçluk takibindeki toplam öğrenci</div></div>
 <div class="card kpi-card"><div class="kpi-label">Bekleyen atama</div><div class="kpi">${pending.length}</div><div class="kpi-foot">Henüz tamamlanmamış görevler</div></div>
 <div class="card kpi-card"><div class="kpi-label">Tekrar sinyali</div><div class="kpi">${low.length}</div><div class="kpi-foot">%${db.threshold} eşiğinin altındaki sonuçlar</div></div>
 <div class="card kpi-card"><div class="kpi-label">Ortalama başarı</div><div class="kpi">%${avg}</div><div class="kpi-foot">Girilen tüm sonuçların ortalaması</div></div>
 <div class="card kpi-card"><div class="kpi-label">İçerik havuzu</div><div class="kpi">${db.resources.length+db.exams.length}</div><div class="kpi-foot">PDF kaynak + online sınav</div></div></div>
 <div class="section"><div class="section-head"><h2>Öncelikli tekrar konuları</h2><span class="muted">En düşük başarılar önce</span></div>
 ${low.length?`<div class="list">${low.slice().sort((a,b)=>a.score-b.score).slice(0,8).map(r=>`<div class="item item-row"><div><div class="cell-title">${studentName(r.studentId)}</div><div class="cell-sub">${r.course} · ${r.topic}</div></div><span class="badge low">%${r.score}</span></div>`).join("")}</div>`:emptyState("Tekrar gerektiren konu yok","Mevcut sonuçlar belirlenen başarı eşiğinin üzerinde.")}</div>`,'dashboard')
}
function studentName(id){return db.students.find(s=>s.id===id)?.name||"Bilinmeyen"}

/* CELL:20-students-profile | layer:frontend | generated-from:v0.8.1 */

/* CELL:20-students-profile | layer:frontend | generated-from:v0.7.2 */
function students(){
 const actions=`<button class="btn primary" onclick="studentModal()">+ Yeni Öğrenci</button>`;
 const rows=db.students.map(s=>`<tr><td><button class="navlink" onclick="openProfile(${s.id})">${s.name}</button><div class="cell-sub">${s.target||"Hedef belirtilmedi"}</div></td><td>${s.grade||"—"}</td><td>${(s.courses||[]).length}</td><td>${(s.courses||[]).map(c=>`<span class="badge neutral">${c}: ${s.levels?.[c]||"Orta"}</span>`).join(" ")||"—"}</td><td><div class="toolbar-group"><button class="btn ghost small" onclick="editStudent(${s.id})">Düzenle</button><button class="btn danger small" onclick="deleteStudent(${s.id})">Sil</button></div></td></tr>`).join("");
 shell(`${pageHead("Öğrenciler","Öğrenci profillerini, ders seçimlerini ve kaynak seviyelerini yönetin.",actions)}${db.students.length?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Sınıf</th><th>Ders Sayısı</th><th>Ders / Seviye</th><th>İşlemler</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Henüz öğrenci yok","Yeni öğrenci ekleyerek koçluk takibini başlatın.")}`,'students')
}
function courseLevelFields(selected=[],levels={}){
 return Object.keys(db.curriculum).map(c=>`<div class="item"><label><input type="checkbox" class="coursecheck" value="${c}" ${selected.includes(c)?"checked":""}> <b>${c}</b></label>
 <select class="courselevel" data-course="${c}"><option>Başlangıç</option><option>Kolay</option><option ${levels[c]==="Orta"?"selected":""}>Orta</option><option ${levels[c]==="Orta-Zor"?"selected":""}>Orta-Zor</option><option ${levels[c]==="Zor"?"selected":""}>Zor</option><option ${levels[c]==="İleri"?"selected":""}>İleri</option></select></div>`).join("")
}
window.studentModal=()=>modal(`<h2>Yeni Öğrenci</h2><div class="formgrid">
<div class="field"><label>Ad Soyad</label><input id="sname"></div><div class="field"><label>Sınıf</label><input id="sgrade"></div>
<div class="field"><label>Hedef</label><input id="starget" value="YKS"></div>
<div class="field"><label>Kayıt Tarihi</label><input id="sregistered" type="date" value="${new Date().toISOString().slice(0,10)}"></div>
<div class="field"><label>Kurs Bitiş Tarihi</label><input id="senddate" type="date"></div>
<div class="field"><label>Haftalık Çalışma Günü</label><input id="sstudydays" type="number" min="1" max="7" value="6"></div>
<div class="field"><label>Günlük Çalışma Süresi (dk)</label><input id="sdailyminutes" type="number" min="30" max="600" step="15" value="120"></div>
<div class="field"><label>AI Dönem Planlama</label><select id="saiauto"><option value="true">Açık</option><option value="false">Kapalı</option></select></div>
</div>
<h3>Koçluk dersleri ve kaynak seviyesi</h3><div class="list">${courseLevelFields()}</div>
<div class="modal-actions"><button class="btn primary" onclick="addStudent()">Kaydet</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
function readStudentCourses(){
 const courses=[...document.querySelectorAll(".coursecheck:checked")].map(x=>x.value),levels={};
 courses.forEach(c=>{levels[c]=document.querySelector(`.courselevel[data-course="${c}"]`)?.value||"Orta"});
 return {courses,levels}
}
window.addStudent=()=>{const name=q("sname").value.trim();if(!name)return alert("Ad soyad gerekli");const x=readStudentCourses();const registeredAt=q("sregistered").value,courseEndDate=q("senddate").value;if(!registeredAt||!courseEndDate||new Date(courseEndDate)<new Date(registeredAt))return alert("Kayıt ve kurs bitiş tarihlerini kontrol edin");db.students.push({id:Date.now(),name,grade:q("sgrade").value,target:q("starget").value,registeredAt,courseEndDate,weeklyStudyDays:Number(q("sstudydays").value)||6,dailyMinutes:Number(q("sdailyminutes").value)||120,aiAutoPlan:q("saiauto").value==="true",courses:x.courses,levels:x.levels});save();closeModal();students()}
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
window.saveStudentEdit=()=>{const id=Number(q("sid").value),s=db.students.find(x=>x.id===id);if(!s)return;const x=readStudentCourses();const registeredAt=q("sregistered").value,courseEndDate=q("senddate").value;if(!registeredAt||!courseEndDate||new Date(courseEndDate)<new Date(registeredAt))return alert("Kurs tarihlerini kontrol edin");s.name=q("sname").value.trim();s.grade=q("sgrade").value;s.target=q("starget").value;s.courses=x.courses;s.levels=x.levels;s.registeredAt=registeredAt;s.courseEndDate=courseEndDate;s.weeklyStudyDays=Number(q("sstudydays").value)||6;s.dailyMinutes=Number(q("sdailyminutes").value)||120;s.aiAutoPlan=q("saiauto").value==="true";save();closeModal();students()}
window.deleteStudent=id=>{if(!confirm("Öğrenci silinsin mi?"))return;db.students=db.students.filter(s=>s.id!==id);db.results=db.results.filter(r=>r.studentId!==id);save();students()}

let selectedProfileStudentId=null;
