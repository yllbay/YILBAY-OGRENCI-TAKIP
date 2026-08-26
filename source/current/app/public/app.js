/* CELL:00-core-store-ui | layer:frontend | generated-from:v0.7.2 */
const STORAGE="yilbay_mvp_065";


const PREV_STORAGE_063="yilbay_mvp_063";


const PREV_STORAGE_062="yilbay_mvp_062";


const PREV_STORAGE_061="yilbay_mvp_061";


const PREV_STORAGE_060="yilbay_mvp_050";


const PREV_STORAGE_045="yilbay_mvp_045";


const PREV_STORAGE="yilbay_mvp_044";


const LEGACY_043="yilbay_mvp_043";


const OLD_STORAGE="yilbay_mvp_040";


const seed={
 students:[{id:1,name:"Bilgehan Özdurak",grade:"12",target:"YKS",registeredAt:"2026-08-26",courseEndDate:"2027-06-01",weeklyStudyDays:6,dailyMinutes:120,aiAutoPlan:true,courses:["TYT Matematik","Problemler","Türkçe"],levels:{"TYT Matematik":"Orta","Problemler":"Orta-Zor","Türkçe":"Orta"}}],
 curriculum:{
   "TYT Matematik":{"Temel Matematik":["Temel Kavramlar","Bölme-Bölünebilme","Rasyonel Sayılar","1. Derece Denklemler","Basit Eşitsizlikler","Mutlak Değer"]},
   "Problemler":{"Problemler":["Sayı Problemleri","Kesir Problemleri","Yaş Problemleri"]},
   "Türkçe":{"Paragraf":["Paragrafta Konu","Paragrafta Başlık","Ana Düşünce"],"Dil Bilgisi":["Yazım Kuralları","Ses Bilgisi"]}
 },
 resources:[
  {id:1,type:"PDF",course:"TYT Matematik",topic:"Mutlak Değer",level:"Orta",title:"Mutlak Değer Ödev 01",url:""},
  {id:2,type:"PDF",course:"Problemler",topic:"Sayı Problemleri",level:"Orta-Zor",title:"Sayı Problemleri Ödev 01",url:""}
 ],
 exams:[
  {id:1,course:"TYT Matematik",topic:"Mutlak Değer",title:"Mutlak Değer Online Test",url:"https://example.com"}
 ],
 results:[
  {id:1,studentId:1,kind:"Ödev",course:"TYT Matematik",topic:"Mutlak Değer",score:58,date:"2026-08-25"},
  {id:2,studentId:1,kind:"Online Sınav",course:"TYT Matematik",topic:"Basit Eşitsizlikler",score:74,date:"2026-08-25"}
 ],
 threshold:70
};


let db=load(), view="dashboard";


function load(){try{
 const current=localStorage.getItem(STORAGE);
 if(current) return normalizeDb(JSON.parse(current));
 const p63=localStorage.getItem(PREV_STORAGE_063);
 if(p63){const migrated=normalizeDb(JSON.parse(p63));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p62=localStorage.getItem(PREV_STORAGE_062);
 if(p62){const migrated=normalizeDb(JSON.parse(p62));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p61=localStorage.getItem(PREV_STORAGE_061);
 if(p61){const migrated=normalizeDb(JSON.parse(p61));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p60=localStorage.getItem(PREV_STORAGE_060);
 if(p60){const migrated=normalizeDb(JSON.parse(p60));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const p45=localStorage.getItem(PREV_STORAGE_045);
 if(p45){const migrated=normalizeDb(JSON.parse(p45));localStorage.setItem(STORAGE,JSON.stringify(migrated));return migrated;}
 const prev=localStorage.getItem(PREV_STORAGE);
 if(prev){const migrated=normalizeDb(JSON.parse(prev)); localStorage.setItem(STORAGE,JSON.stringify(migrated)); return migrated;}
 const legacy43=localStorage.getItem(LEGACY_043);
 if(legacy43){const migrated=normalizeDb(JSON.parse(legacy43)); localStorage.setItem(STORAGE,JSON.stringify(migrated)); return migrated;}
 const old=localStorage.getItem(OLD_STORAGE);
 if(old){const migrated=normalizeDb(JSON.parse(old)); localStorage.setItem(STORAGE,JSON.stringify(migrated)); return migrated;}
 return normalizeDb(structuredClone(seed))
}catch{return normalizeDb(structuredClone(seed))}}


function normalizeDb(x){
 x.assignments??=[];
 x.weeklyPlans??={};
 x.aiPlans??={};
 x.videoSuggestions??={};
 x.homeworkAnalyses??=[];
 x.repeatSignals??=[];
 x.threshold??=70;
 return x
}


function save(){localStorage.setItem(STORAGE,JSON.stringify(db))}


const app=()=>document.getElementById("app");


const scoreClass=n=>n>=80?"good":n>=60?"mid":"low";


function initials(name=""){return name.split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase()||"Ö"}


function tableWrap(html){return `<div class="table-wrap">${html}</div>`}


function emptyState(title,text){return `<div class="empty"><strong>${title}</strong>${text}</div>`}


function pageHead(title,desc,actions=""){return `<div class="page-head"><div class="page-title"><h1>${title}</h1><p>${desc}</p></div><div class="page-actions">${actions}</div></div>`}


function shell(content,active=view){app().innerHTML=`<div class="top"><div class="brand-wrap"><div class="brandmark">Y</div><div><div class="brand">YILBAY Öğrenci Takip</div><div class="brand-sub">Akademik Koçluk Yönetim Sistemi</div></div></div><div class="top-right"><span class="version">v0.11.1</span></div></div><div class="layout"><aside>
<div class="nav-section">Yönetim</div>${nav("dashboard","Genel Bakış",active)}${nav("students","Öğrenciler",active)}${nav("profile","Öğrenci Profili",active)}
<div class="nav-section">Akademik İçerik</div>${nav("curriculum","Ders ve Üniteler",active)}${nav("resources","Kaynak Havuzu",active)}${nav("exams","Online Sınavlar",active)}
<div class="nav-section">Operasyon</div>${nav("assignments","Atamalar",active)}${nav("results","Başarı Sonuçları",active)}${nav("program","Haftalık Program",active)}
<div class="nav-section">Sistem</div>${nav("integrations","AI ve API Entegrasyonları",active)}
</aside><main><div class="page">${content}</div></main></div>`}


function nav(k,t,a){return `<button class="nav ${a===k?"active":""}" onclick="go('${k}')">${t}</button>`}


window.go=k=>{view=k;render()}
function render(){({dashboard,students,profile,curriculum,resources,exams,assignments,results,program,integrations}[view]||dashboard)()}

/* CELL:10-dashboard | layer:frontend | generated-from:v0.11.1 */

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

/* CELL:20-students-profile | layer:frontend | generated-from:v0.11.1 */

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

/* CELL:30-curriculum | layer:frontend | generated-from:v0.11.1 */

/* CELL:30-curriculum | layer:frontend | generated-from:v0.7.2 */
function curriculum(){
 let cards="";for(const [course,units] of Object.entries(db.curriculum)){cards+=`<div class="card"><div class="section-head"><h2 style="margin:0">${course}</h2><span class="badge info">${Object.values(units).reduce((n,x)=>n+x.length,0)} konu</span></div>`;for(const [u,topics] of Object.entries(units)){cards+=`<div class="item"><div class="cell-title">${u}</div><div style="margin-top:8px">${topics.map(t=>`<span class="badge neutral">${t}</span>`).join(" ")}</div></div>`}cards+="</div>"}
 shell(`${pageHead("Ders ve Üniteler","Ders, ünite ve alt konu yapısını yönetin.",`<button class="btn primary" onclick="currModal()">+ Müfredat Ekle</button>`)}<div class="list">${cards||emptyState("Müfredat boş","Ders ve konu ekleyerek başlayın.")}</div>`,"curriculum")
}
window.currModal=()=>modal(`<h2>Müfredat Ekle</h2><div class="formgrid"><div class="field"><label>Ders</label><input id="ccourse"></div><div class="field"><label>Ünite</label><input id="cunit"></div><div class="field"><label>Alt ünite / konu</label><input id="ctopic"></div></div><div class="modal-actions"><button class="btn primary" onclick="addCurr()">Kaydet</button></div>`)
window.addCurr=()=>{let c=q("ccourse").value.trim(),u=q("cunit").value.trim(),t=q("ctopic").value.trim();if(!c||!u||!t)return alert("Tüm alanlar gerekli");db.curriculum[c]??={};db.curriculum[c][u]??=[];if(!db.curriculum[c][u].includes(t))db.curriculum[c][u].push(t);save();closeModal();curriculum()}
function topicOptions(){let out="";for(const [c,units] of Object.entries(db.curriculum))for(const topics of Object.values(units))for(const t of topics)out+=`<option data-course="${c}" value="${c}|||${t}">${c} — ${t}</option>`;return out}

/* CELL:40-resources | layer:frontend | generated-from:v0.11.1 */

/* CELL:40-resources | layer:frontend | generated-from:v0.7.2 */
function resources(){
 const rows=db.resources.map(r=>`<tr><td><div class="cell-title">${r.title}</div><div class="cell-sub">${r.type||"PDF"}${r.driveSource?" · Drive":""}</div></td><td>${r.course||"-"}</td><td>${r.unit||"-"}</td><td>${r.subtopic||r.topic||"-"}</td><td><span class="badge neutral">${r.level||"-"}</span></td><td>${Number(r.questionCount)>0?Number(r.questionCount):"-"}</td><td>${r.answerKeyDriveFileId?'<span class="badge success">Bağlı</span>':'<span class="badge neutral">Yok</span>'}</td><td><button class="btn small" onclick="resourceEditModal(${r.id})">Düzenle</button></td></tr>`).join("");
 shell(`${pageHead("Kaynak Havuzu","PDF ödev ve çalışma kaynaklarını ders, ünite, alt konu ve zorluk düzeyine göre yönetin.",`<button class="btn primary" onclick="resourceModal()">+ Kaynak Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Kaynak</th><th>Ders</th><th>Ünite</th><th>Alt Konu</th><th>Seviye</th><th>Soru</th><th>Cevap Anahtarı</th><th></th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Kaynak bulunamadı","İlk PDF kaynağınızı ekleyin.")}`,"resources")
}
window.resourceEditModal=(id)=>{const r=db.resources.find(x=>x.id===id);if(!r)return;modal(`<h2>Kaynak Bilgilerini Düzenle</h2><div class="formgrid"><div class="field"><label>Başlık</label><input id="ertitle" value="${String(r.title||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;')}"></div><div class="field"><label>Ünite</label><input id="erunit" value="${String(r.unit||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;')}"></div><div class="field"><label>Alt Konu</label><input id="ersubtopic" value="${String(r.subtopic||r.topic||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;')}"></div><div class="field"><label>Soru Sayısı</label><input id="erquestioncount" type="number" min="0" value="${Number(r.questionCount)||0}"></div><div class="field"><label>Cevap Anahtarı Drive File ID</label><input id="eranswerkey" value="${String(r.answerKeyDriveFileId||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;')}"></div></div><div class="modal-actions"><button class="btn primary" onclick="saveResourceMetadata(${id})">Kaydet</button></div>`)}
window.saveResourceMetadata=(id)=>{const r=db.resources.find(x=>x.id===id);if(!r)return;r.title=q('ertitle').value.trim()||r.title;r.unit=q('erunit').value.trim();r.subtopic=q('ersubtopic').value.trim()||r.topic;r.questionCount=Math.max(0,Number(q('erquestioncount').value)||0);r.answerKeyDriveFileId=q('eranswerkey').value.trim();save();closeModal();resources()}
window.resourceModal=()=>modal(`<h2>Kaynak Ekle</h2><div class="formgrid"><div class="field"><label>Başlık</label><input id="rtitle"></div><div class="field"><label>Konu</label><select id="rtopic">${topicOptions()}</select></div><div class="field"><label>Ünite</label><input id="runit"></div><div class="field"><label>Alt Konu</label><input id="rsubtopic"></div><div class="field"><label>Zorluk</label><select id="rlevel"><option>Başlangıç</option><option>Kolay</option><option>Orta</option><option>Orta-Zor</option><option>Zor</option><option>İleri</option></select></div><div class="field"><label>Soru Sayısı</label><input id="rquestioncount" type="number" min="0"></div><div class="field"><label>Drive bağlantısı / File ID</label><input id="rurl"></div><div class="field"><label>Cevap Anahtarı Drive File ID</label><input id="ranswerkey"></div></div><div class="modal-actions"><button class="btn primary" onclick="addResource()">Kaydet</button></div>`)
window.addResource=()=>{const [course,topic]=q("rtopic").value.split("|||");db.resources.push({id:Date.now(),type:"PDF",course,topic,unit:q("runit").value.trim(),subtopic:q("rsubtopic").value.trim()||topic,level:q("rlevel").value,questionCount:Math.max(0,Number(q("rquestioncount").value)||0),answerKeyDriveFileId:q("ranswerkey").value.trim(),title:q("rtitle").value||topic+" Kaynak",url:q("rurl").value});save();closeModal();resources()}
function exams(){
 const rows=db.exams.map(e=>`<tr><td><div class="cell-title">${e.title}</div></td><td>${e.course}</td><td>${e.topic}</td><td>${e.url?`<a href="${e.url}" target="_blank">Sınavı aç</a>`:"—"}</td></tr>`).join("");
 shell(`${pageHead("Online Sınavlar","Online test ve sınav bağlantılarını konu bazında yönetin.",`<button class="btn primary" onclick="examModal()">+ Sınav Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Sınav</th><th>Ders</th><th>Konu</th><th>Bağlantı</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Online sınav yok","İlk sınav bağlantısını ekleyin.")}`,"exams")
}
window.examModal=()=>modal(`<h2>Online Sınav Ekle</h2><div class="formgrid"><div class="field"><label>Başlık</label><input id="etitle"></div><div class="field"><label>Konu</label><select id="etopic">${topicOptions()}</select></div><div class="field"><label>Link</label><input id="eurl"></div></div><div class="modal-actions"><button class="btn primary" onclick="addExam()">Kaydet</button></div>`)
window.addExam=()=>{const [course,topic]=q("etopic").value.split("|||");db.exams.push({id:Date.now(),course,topic,title:q("etitle").value||topic+" Online Test",url:q("eurl").value});save();closeModal();exams()}

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.11.1 */

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.7.2 */
function assignments(){
 const rows=db.assignments.slice().reverse().map(a=>`<tr><td><div class="cell-title">${studentName(a.studentId)}</div></td><td><span class="badge info">${a.kind}</span></td><td><div class="cell-title">${a.title}</div><div class="cell-sub">${a.course} · ${a.topic}</div></td><td><span class="badge ${a.status==="Tamamlandı"?"good":"mid"}">${a.status}</span></td><td><div class="row-actions">${a.status==="Tamamlandı"?'<span class="muted">Tamamlandı</span>':a.status==="Öğretmen Kontrolü"?`<button class="btn primary small" onclick="reviewHomeworkAnalysis(${a.id})">AI analizini kontrol et</button><button class="btn ghost small" onclick="analyzeAssignment(${a.id})">Yeniden tara</button>`:`<button class="btn ghost small" onclick="completeAssignment(${a.id})">Manuel sonuç</button>${a.kind==="PDF Kaynak"?`<button class="btn primary small" onclick="analyzeAssignment(${a.id})">AI ile ödevi tara</button>`:''}`}<button class="btn danger small" onclick="deleteAssignment(${a.id})">Sil</button></div></td></tr>`).join('');
 const actions='<button class="btn ghost" onclick="scannedPdfHistory()">Taranmış PDFler</button> '+(db.assignments.length?'<button class="btn danger" onclick="clearAssignments()">Atama Listesini Temizle</button> ':'')+'<button class="btn primary" onclick="assignmentModal()">+ Yeni Atama</button>';
 shell(`${pageHead('Atamalar','Öğrencilere kaynak ve online sınav atayın, tamamlanma durumunu takip edin.',actions)}${rows?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Tür</th><th>İçerik</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState('Henüz atama yok','Yeni atama oluşturarak çalışma akışını başlatın.')}`,'assignments')
}
window.deleteAssignment=id=>{const x=db.assignments.find(a=>Number(a.id)===Number(id));if(!x||!confirm('Bu atama listeden silinsin mi? Akademik sonuçlar ve AI analiz geçmişi korunur.'))return;db.assignments=db.assignments.filter(a=>Number(a.id)!==Number(id));save();assignments()}
window.clearAssignments=()=>{if(!db.assignments.length||!confirm('Atamalar ekranındaki TÜM kayıtlar silinsin mi? Akademik sonuçlar ve AI analiz geçmişi korunur.'))return;db.assignments=[];save();assignments()}

window.scannedPdfHistory=()=>{const xs=db.homeworkAnalyses.slice().reverse(),rows=xs.map(function(x){return '<tr><td>'+studentName(x.studentId)+'</td><td>'+(x.fileName||'Ödev PDF')+'</td><td>'+(x.date||'—')+'</td><td>'+(x.totalQuestions||0)+'</td><td><button class="btn danger small" onclick="deleteScannedPdfRecord('+Number(x.id)+')">Sil</button></td></tr>'}).join(''),clear=xs.length?'<button class="btn danger" onclick="clearScannedPdfRecords()">Tüm taranmış PDF kayıtlarını sil</button>':'';modal('<h2>İşlenen / Taranmış PDFler</h2><p class="muted">Yerel ödev dosyasının kendisi kalıcı tutulmaz. Bu liste analiz kaydını ve varsa yerel karne PDF dosyasını yönetir. Drive üzerindeki asıl dosya silinmez.</p>'+(rows?tableWrap('<table><thead><tr><th>Öğrenci</th><th>PDF</th><th>Tarih</th><th>Soru</th><th>İşlem</th></tr></thead><tbody>'+rows+'</tbody></table>'):emptyState('Taranmış PDF yok','AI ile analiz edilen ödevler burada listelenecek.'))+'<div class="modal-actions">'+clear+' <button class="btn ghost" onclick="closeModal()">Kapat</button></div>')}
window.deleteScannedPdfRecord=async id=>{const x=db.homeworkAnalyses.find(v=>Number(v.id)===Number(id));if(!x||!confirm('Bu taranmış PDF analiz kaydı silinsin mi? Drive veya bilgisayardaki asıl dosya etkilenmez.'))return;if(x.pdfReportUrl){try{await fetch(x.pdfReportUrl,{method:'DELETE'})}catch{}}db.homeworkAnalyses=db.homeworkAnalyses.filter(v=>Number(v.id)!==Number(id));save();scannedPdfHistory()}
window.clearScannedPdfRecords=async()=>{if(!db.homeworkAnalyses.length||!confirm('Tüm taranmış PDF analiz kayıtları ve yerel karne PDF dosyaları silinsin mi? Asıl dosyalar etkilenmez.'))return;for(const x of db.homeworkAnalyses){if(x.pdfReportUrl){try{await fetch(x.pdfReportUrl,{method:'DELETE'})}catch{}}}db.homeworkAnalyses=[];save();scannedPdfHistory()}
window.assignmentModal=()=>{modal(`<h2>Yeni Atama</h2><div class="formgrid">
<div class="field"><label>Öğrenci</label><select id="astudent">${db.students.map(s=>`<option value="${s.id}">${s.name}</option>`).join("")}</select></div>
<div class="field"><label>Atama türü</label><select id="akind" onchange="refreshAssignmentItems()"><option>PDF Kaynak</option><option>Online Sınav</option></select></div>
<div class="field" style="grid-column:1/-1"><label>İçerik</label><select id="aitem"></select></div>
</div><div class="modal-actions"><button class="btn primary" onclick="addAssignment()">Ata</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>`);refreshAssignmentItems()}
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
 const analyses=db.homeworkAnalyses.slice().reverse().slice(0,50).map(x=>`<tr><td>${studentName(x.studentId)}</td><td>${x.course} / ${x.topic}</td><td><span class="badge ${x.needsTeacherReview&&!x.teacherReviewed?"mid":"good"}">${x.needsTeacherReview&&!x.teacherReviewed?"Öğretmen Kontrolü":x.teacherReviewed?"Öğretmen Onaylı":"AI Kesinleştirdi"}</span></td><td>%${Math.round(Number(x.teacherScore??x.scorePercent)||0)}</td><td>%${Math.round((Number(x.confidence)||0)*100)}</td><td>${Number(x.costTry||0).toFixed(4)} TL</td><td><button class="btn danger small" onclick="deleteHomeworkAnalysis(${x.id})">Sil</button></td></tr>`).join("");
 const clear= db.homeworkAnalyses.length?'<button class="btn danger small" onclick="clearHomeworkAnalyses()">Tüm Analiz Geçmişini Temizle</button>':'';
 shell(`${pageHead("Başarı Sonuçları","Ödev ve online sınav başarılarını kaydedin. Adaptif tekrar eşiği %"+db.threshold,`<button class="btn primary" onclick="resultModal()">+ Sonuç Gir</button>`)}${rows?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Tür</th><th>Konu</th><th>Başarı</th><th>Tarih</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Sonuç bulunamadı","İlk ödev veya sınav sonucunu girin.")}<div class="section"><div class="section-head"><h2>AI Ödev Analiz Geçmişi</h2><div>${clear}</div></div>${analyses?tableWrap(`<table><thead><tr><th>Öğrenci</th><th>Ders / Konu</th><th>Durum</th><th>Başarı</th><th>AI Güveni</th><th>Maliyet</th><th>İşlem</th></tr></thead><tbody>${analyses}</tbody></table>`):emptyState("AI analiz geçmişi yok","İlk AI ödev taramasından sonra burada görünecek.")}</div>`,"results")
}
window.deleteHomeworkAnalysis=async id=>{const x=db.homeworkAnalyses.find(v=>Number(v.id)===Number(id));if(!x||!confirm('Bu AI analiz kaydı silinsin mi? Akademik sonuç kaydı korunur.'))return;if(x.pdfReportUrl){try{await fetch(x.pdfReportUrl,{method:'DELETE'})}catch{}}db.homeworkAnalyses=db.homeworkAnalyses.filter(v=>Number(v.id)!==Number(id));save();results()}
window.clearHomeworkAnalyses=async()=>{if(!db.homeworkAnalyses.length||!confirm('Tüm AI ödev analiz geçmişi ve yerel PDF karneleri silinsin mi? Akademik sonuçlar korunur.'))return;for(const x of db.homeworkAnalyses){if(x.pdfReportUrl){try{await fetch(x.pdfReportUrl,{method:'DELETE'})}catch{}}}db.homeworkAnalyses=[];save();results()}
window.resultModal=()=>modal(`<h2>Sonuç Gir</h2><div class="formgrid"><div class="field"><label>Öğrenci</label><select id="xstudent">${db.students.map(s=>`<option value="${s.id}">${s.name}</option>`).join("")}</select></div><div class="field"><label>Tür</label><select id="xkind"><option>Ödev</option><option>Online Sınav</option></select></div><div class="field"><label>Konu</label><select id="xtopic">${topicOptions()}</select></div><div class="field"><label>Başarı %</label><input id="xscore" type="number" min="0" max="100"></div></div><div class="modal-actions"><button class="btn primary" onclick="addResult()">Kaydet</button></div>`)
window.addResult=()=>{const [course,topic]=q("xtopic").value.split("|||"),score=Math.max(0,Math.min(100,Number(q("xscore").value)));db.results.push({id:Date.now(),studentId:Number(q("xstudent").value),kind:q("xkind").value,course,topic,score,date:new Date().toISOString().slice(0,10)});save();closeModal();results()}

/* CELL:70-planner | layer:frontend | generated-from:v0.11.1 */

/* CELL:70-planner | layer:frontend | generated-from:v0.7.2 */
let selectedStudentId=null;


const DAY_NAMES=["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"];


function buildPlanItems(s){
 const latest={};
 db.results.filter(r=>r.studentId===s.id).forEach(r=>{const k=r.course+"|||"+r.topic;if(!latest[k]||String(r.date)>=String(latest[k].date))latest[k]=r});
 const repeats=Object.values(latest).filter(r=>r.score<db.threshold).map(r=>{
   const wanted=s.levels?.[r.course]||"Orta";
   const res=db.resources.find(x=>x.course===r.course&&x.topic===r.topic&&x.level===wanted)||db.resources.find(x=>x.course===r.course&&x.topic===r.topic);
   const exam=db.exams.find(x=>x.course===r.course&&x.topic===r.topic);
   return {type:"Tekrar",course:r.course,topic:r.topic,level:wanted,resource:res?.title||"Uygun kaynak ekleyin",exam:exam?.title||"—",reason:`Son başarı %${r.score}`,priority:0}
 });
 const pending=db.assignments.filter(a=>a.studentId===s.id&&a.status!=="Tamamlandı").map(a=>({
   type:"Atama",course:a.course,topic:a.topic,level:s.levels?.[a.course]||"Orta",
   resource:a.kind==="PDF Kaynak"?a.title:"—",exam:a.kind==="Online Sınav"?a.title:"—",
   reason:"Bekleyen atama",priority:1
 }));
 const map=new Map();
 [...repeats,...pending].forEach(x=>{const k=x.type+"|||"+x.course+"|||"+x.topic+"|||"+x.resource+"|||"+x.exam;if(!map.has(k))map.set(k,x)});
 return [...map.values()].sort((a,b)=>a.priority-b.priority||a.course.localeCompare(b.course));
}


function generateWeeklyPlan(){
 const s=db.students.find(x=>x.id===selectedStudentId);if(!s)return;
 const items=buildPlanItems(s);
 const days=Object.fromEntries(DAY_NAMES.map(d=>[d,[]]));
 items.forEach((item,i)=>days[DAY_NAMES[i%7]].push(item));
 db.weeklyPlans[String(s.id)]={generatedAt:new Date().toISOString(),days};
 save();program()
}


function program(){
 if(!db.students.length){shell(`${pageHead("Haftalık Program","Öğrenciye özel adaptif çalışma planı.")}${emptyState("Öğrenci bulunamadı","Program oluşturmak için önce öğrenci ekleyin.")}`,"program");return}
 if(!selectedStudentId||!db.students.some(s=>s.id===selectedStudentId))selectedStudentId=db.students[0].id;
 const s=db.students.find(x=>x.id===selectedStudentId),key=String(s.id),saved=db.weeklyPlans?.[key];
 const preview=saved?.days||(()=>{const days=Object.fromEntries(DAY_NAMES.map(d=>[d,[]]));buildPlanItems(s).forEach((x,i)=>days[DAY_NAMES[i%7]].push(x));return days})();
 const total=Object.values(preview).reduce((n,a)=>n+a.length,0);
 const actions=`<div class="toolbar-group"><select onchange="selectedStudentId=Number(this.value);program()">${db.students.map(x=>`<option value="${x.id}" ${x.id===s.id?"selected":""}>${x.name}</option>`).join("")}</select><button class="btn ghost" onclick="generateWeeklyPlan()">Kural Tabanlı Plan</button><button class="btn primary" onclick="generateAiMasterPlan()">AI ile Dönem Planı Üret</button></div>`;
 shell(`${pageHead("Haftalık Program","Adaptif planlayıcı tekrar ihtiyaçlarını ve bekleyen atamaları 7 güne dengeli dağıtır.",actions)}
 <div class="notice"><div><b>Planlama kuralı</b>Önce %${db.threshold} altındaki konular, ardından bekleyen atamalar. Toplam görev: ${total}. ${saved?`Son kayıt: ${new Date(saved.generatedAt).toLocaleString("tr-TR")}`:"Henüz kaydedilmedi; aşağıdaki görünüm önizlemedir."}${db.aiPlans?.[key]?`<br><b>Dönem planı:</b> ${db.aiPlans[key].usedAi?"OpenAI ile üretildi":"kural tabanlı fallback"} · ${db.aiPlans[key].plan?.weeks?.length||0} hafta${db.aiPlans[key].plan?.weeklyCapacityMinutes?` · haftalık kapasite ${db.aiPlans[key].plan.weeklyCapacityMinutes} dk`:""}${db.aiPlans[key].plan?.overload?` · <span class="badge low">${db.aiPlans[key].plan.overflowCount} konu kapasite dışı</span>`:""}`:""}</div></div>
 <div class="section"><div class="weekgrid">${DAY_NAMES.map(d=>`<div class="daycard"><h3>${d}</h3>${preview[d].map(x=>`<div class="task"><div class="task-title">${x.type} · ${x.course}</div><div class="task-sub">${x.topic}<br>${x.resource!=="—"?x.resource:x.exam}</div><div class="task-actions"><span class="badge ${x.type==="Tekrar"?"low":"mid"}">${x.reason}</span><button class="link-btn" onclick='findTopicVideo(${JSON.stringify(x.course)},${JSON.stringify(x.topic)})'>Video bul</button></div></div>`).join("")||`<div class="muted">Görev yok</div>`}</div>`).join("")}</div></div>`,"program")
}

/* CELL:80-api-client | layer:frontend | generated-from:v0.11.1 */

/* CELL:80-api-client | layer:frontend | generated-from:v0.7.2 */
async function apiJson(url,body=null){
 const opt=body===null?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)};
 const r=await fetch(url,opt),data=await r.json().catch(()=>({}));
 if(!r.ok||data.ok===false)throw new Error(data.error||`HTTP ${r.status}`);
 return data
}

/* CELL:90-integrations | layer:frontend | generated-from:v0.11.1 */

/* CELL:90-integrations | layer:frontend | generated-from:v0.7.2 */
function integrations(){
 shell(`${pageHead("AI ve API Entegrasyonları","OpenAI ile adaptif planlama/ödev analizi, YouTube ile konu anlatım videosu seçimi. API anahtarları tarayıcıya kaydedilmez.",`<button class="btn primary" onclick="testOpenAIConnection()">OpenAI Bağlantısını Test Et</button>`)}
 <div id="integrationStatus"><div class="card">Entegrasyon durumu okunuyor…</div></div>
 <div class="section"><div class="section-head"><h2>Güvenlik</h2></div><div class="notice"><div><b>Sunucu tarafı anahtar saklama</b>Anahtarlar LocalStorage veya uygulama JavaScript dosyasına yazılmaz. Kalıcı paketin <code>runtime</code> alanında tutulur ve mevcut teşhis raporuna eklenmez.</div></div></div>`,"integrations");
 loadIntegrationStatus()
}


async function loadIntegrationStatus(){
 try{
  const s=await apiJson("/api/integrations/status");
  const c=await apiJson("/api/ai/costs");
  q("integrationStatus").innerHTML=`<div class="integration-grid">
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">OpenAI</div><div class="cell-sub">Planlama + ödev vision analizi</div></div><span class="badge ${s.openai.configured?"good":"mid"}">${s.openai.configured?"Bağlı":"Anahtar gerekli"}</span></div><div class="integration-meta">Model: <b>${s.openai.model}</b><br>Kaynak: <b>${s.openai.source==="windows-credential-manager"?"Windows Kimlik Bilgileri Yöneticisi":s.openai.source==="environment"?"Ortam değişkeni":s.openai.source==="manual"?"Manuel ayar":"Yok"}</b>${s.openai.source==="windows-credential-manager"?` · ${s.openai.credentialTarget}`:""}</div></div>
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">YouTube Data API</div><div class="cell-sub">Konu anlatım videosu arama</div></div><span class="badge ${s.youtube.configured?"good":"mid"}">${s.youtube.configured?"Bağlı":"Anahtar gerekli"}</span></div><div class="integration-meta">Türkçe video araması ve güvenli arama</div></div>
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">Google Drive</div><div class="cell-sub">PDF kaynak havuzu</div></div><span class="badge info">Aşama 2</span></div><div class="integration-meta">Şimdilik kaynak kayıtlarındaki Drive bağlantıları kullanılır; OAuth bağlantısı sonraki adım.</div></div>
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">Bu ay AI maliyeti</div><div class="cell-sub">${c.operations} ücretli AI işlemi</div></div><span class="badge ${c.budgetPercent<70?"good":c.budgetPercent<90?"mid":"low"}">${c.totalTry.toFixed(2)} TL</span></div><div class="integration-meta">Bütçe: ${c.budgetTry.toFixed(0)} TL · Kalan: ${c.remainingTry.toFixed(2)} TL · İşlem ort.: ${c.averageTry.toFixed(3)} TL</div></div>
  </div>
  <div class="grid">
   <div class="card kpi-card"><div class="kpi-label">Planlama</div><div class="kpi">${Number(c.byOperation.plan||0).toFixed(2)} TL</div><div class="kpi-foot">AI dönem planı</div></div>
   <div class="card kpi-card"><div class="kpi-label">Ödev analizi</div><div class="kpi">${Number(c.byOperation.homework_analysis||0).toFixed(2)} TL</div><div class="kpi-foot">PDF / vision değerlendirme</div></div>
   <div class="card kpi-card"><div class="kpi-label">Kur</div><div class="kpi">${c.usdTry.toFixed(2)}</div><div class="kpi-foot">1 USD → TL maliyet hesabı</div></div>
  </div>
  <div class="section"><div class="section-head"><h2>Google Drive Kaynak Havuzu</h2><span class="muted">Salt-okunur bağlantı · Dosya adı: DERS__KONU__SEVIYE__BASLIK.pdf</span></div><div id="drivePanel"><div class="card">Drive durumu okunuyor…</div></div></div>
  <div class="section"><button class="btn primary" onclick="integrationSettingsModal()">API Ayarlarını Aç</button></div>`
 }catch(e){q("integrationStatus").innerHTML=`<div class="notice error">${e.message}</div>`}
  loadDriveStatus();
}


window.integrationSettingsModal=()=>modal(`<h2>API Ayarları</h2><p class="muted">Mevcut anahtarı korumak için alanı boş bırakabilirsiniz.</p><div class="formgrid">
 <div class="field"><label>OpenAI API Key</label><input id="openaiKey" type="password" autocomplete="off" placeholder="sk-..."></div>
 <div class="field"><label>OpenAI Modeli</label><select id="openaiModel"><option value="gpt-5.6-luna">GPT-5.6 Luna — düşük maliyet</option><option value="gpt-5.6-terra">GPT-5.6 Terra — daha yüksek kalite</option><option value="gpt-5.6-sol">GPT-5.6 Sol — en yüksek kalite</option></select></div>
 <div class="field" style="grid-column:1/-1"><label>YouTube Data API Key</label><input id="youtubeKey" type="password" autocomplete="off" placeholder="AIza..."></div><div class="field"><label>Google Drive OAuth Client ID</label><input id="driveClientId" autocomplete="off" placeholder="...apps.googleusercontent.com"></div><div class="field"><label>Google Drive OAuth Client Secret</label><input id="driveClientSecret" type="password" autocomplete="off" placeholder="GOCSPX-..."></div><div class="field" style="grid-column:1/-1"><label>Google Drive Kaynak Klasörü ID</label><input id="driveFolderId" autocomplete="off" placeholder="Drive klasör ID"></div>
 <div class="field"><label>USD/TL Maliyet Kuru</label><input id="usdTry" type="number" step="0.01" min="1" value="48.12"></div>
 <div class="field"><label>Aylık AI Bütçe Limiti (TL)</label><input id="monthlyBudgetTry" type="number" step="10" min="10" value="1000"></div>
 </div><div class="modal-actions"><button class="btn primary" onclick="saveIntegrationSettings()">Kaydet</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
window.saveIntegrationSettings=async()=>{
 try{
  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;
  const driveClientId=q("driveClientId").value.trim(),driveClientSecret=q("driveClientSecret").value.trim(),driveFolderId=q("driveFolderId").value.trim();
  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;
  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",driveClientId:driveClientId||"__KEEP__",driveClientSecret:driveClientSecret||"__KEEP__",driveFolderId:driveFolderId||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});
  closeModal();integrations()
 }catch(e){alert("Ayar kaydedilemedi: "+e.message)}
}
window.testOpenAIConnection=async()=>{
 const btn=[...document.querySelectorAll("button")].find(x=>x.textContent.includes("OpenAI Bağlantısını Test Et"));
 const old=btn?.textContent;if(btn){btn.disabled=true;btn.textContent="Test ediliyor…"}
 try{
  const r=await apiJson("/api/ai/ping",{});
  alert(`OpenAI bağlantısı başarılı.\nModel: ${r.model}\nGecikme: ${r.latencyMs} ms${r.cost?`\nMaliyet: ${Number(r.cost.try||0).toFixed(4)} TL`:""}`);
  loadIntegrationStatus();
 }catch(e){alert("OpenAI bağlantı testi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent=old||"OpenAI Bağlantısını Test Et"}}
}

/* CELL:100-ai-planner | layer:frontend | generated-from:v0.11.1 */

/* CELL:100-ai-planner | layer:frontend | generated-from:v0.7.2 */
window.generateAiMasterPlan=async()=>{
 const s=db.students.find(x=>x.id===selectedStudentId);if(!s)return;
 const key=String(s.id);
 const oldText=document.querySelector(".page-actions .btn.primary")?.textContent;
 const btn=document.querySelector(".page-actions .btn.primary");if(btn){btn.disabled=true;btn.textContent="AI planlıyor…"}
 try{
  const data=await apiJson("/api/ai/plan",{student:s,curriculum:db.curriculum,results:db.results.filter(r=>r.studentId===s.id),resources:db.resources});
  db.aiPlans[key]=data;
  const weeks=data.plan?.weeks||[];
  const now=new Date(),start=new Date(s.registeredAt||now),idx=Math.max(0,Math.min(weeks.length-1,Math.floor((now-start)/(7*864e5))));
  const source=weeks[idx]?.items||weeks[0]?.items||[];
  const allowed=DAY_NAMES.slice(0,Math.max(1,Math.min(7,s.weeklyStudyDays||6))),days=Object.fromEntries(DAY_NAMES.map(d=>[d,[]]));
  source.forEach((x,i)=>{
    const res=db.resources.find(r=>r.id===x.resourceId);
    days[allowed[i%allowed.length]].push({type:x.type||"Yeni Konu",course:x.course,topic:x.topic,level:s.levels?.[x.course]||"Orta",resource:res?.title||"Kaynak seçilecek",exam:"—",reason:x.reason||"AI dönem planı",priority:x.priority==="high"?0:1})
  });
  db.weeklyPlans[key]={generatedAt:new Date().toISOString(),days,source:"ai"};
  save();program();
  alert(data.usedAi?`AI dönem planı oluşturuldu.${data.cost?`\nBu işlem: ${Number(data.cost.try||0).toFixed(3)} TL`:""}`:"API anahtarı olmadığı için kural tabanlı dönem planı oluşturuldu.")
 }catch(e){alert("AI planlama hatası: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent=oldText||"AI ile Dönem Planı Üret"}}
}

/* CELL:110-youtube | layer:frontend | generated-from:v0.11.1 */

/* CELL:110-youtube | layer:frontend | generated-from:v0.7.2 */
window.findTopicVideo=async(course,topic)=>{
 try{
  const key=course+"|||"+topic;
  modal(`<h2>Konu Anlatım Videosu</h2><div id="videoResults"><div class="muted">YouTube aranıyor…</div></div><div class="modal-actions"><button class="btn ghost" onclick="closeModal()">Kapat</button></div>`);
  const data=await apiJson("/api/youtube/search",{query:`${course} ${topic} konu anlatımı YKS TYT AYT`,maxResults:5});
  db.videoSuggestions[key]=data.videos;save();
  q("videoResults").innerHTML=data.videos.length?`<div class="video-list">${data.videos.map((v,i)=>`<a class="video-row" href="${v.url}" target="_blank" rel="noopener"><div class="video-rank">${i+1}</div><div><div class="cell-title">${v.title}</div><div class="cell-sub">${v.channelTitle}</div></div></a>`).join("")}</div>`:emptyState("Video bulunamadı","Arama sorgusunu veya API ayarını kontrol edin.")
 }catch(e){if(q("videoResults"))q("videoResults").innerHTML=`<div class="notice error">${e.message}</div>`;else alert(e.message)}
}

/* CELL:120-ai-homework | layer:frontend | generated-from:v0.11.1 */

/* CELL:120-ai-homework | layer:frontend | generated-from:v0.7.2 */
window.analyzeAssignment=id=>{
 const a=db.assignments.find(x=>x.id===id);if(!a)return;const rc=assignmentResourceContext(a);
 modal(`<h2>AI ile Ödev Analizi</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} · ${a.course} / ${a.topic}</p>
 <div class="field"><label>Ödev dosyası kaynağı</label><select id="homeworkSource" onchange="toggleHomeworkSource()"><option value="local">Bu bilgisayardan</option><option value="drive">Google Drive</option></select></div>
 <div id="homeworkLocalWrap" class="field"><label>Öğrencinin tamamladığı PDF veya görsel</label><input id="homeworkFile" type="file" accept=".pdf,image/png,image/jpeg,image/webp"></div>
 <div id="homeworkDriveWrap" class="field" style="display:none"><label>Drive dosya bağlantısı veya kimliği</label><input id="homeworkDriveInput" placeholder="https://drive.google.com/file/d/... veya dosya kimliği"></div>
 <div class="field"><label>Cevap anahtarı (opsiyonel)</label><textarea id="answerKey" rows="4" placeholder="Örn: 1-A, 2-C, 3-B..."></textarea></div>
 <div class="notice"><div><b>Doğrudan Luna Vision</b>Seçtiğiniz öğrenci PDF/görseli doğrudan Luna’ya gönderilir. Bilgisayardan yüklemede Drive kontrol edilmez.</div></div>
 <div class="notice"><div><b>Analiz kapsamı</b>AI; doğru, yanlış ve boşları belirler. Ayrıca öğrencinin el yazısı çözüm adımlarını, kullandığı yöntemi, ilk hata adımını, kavramsal/işlemsel/dikkat hatalarını, gereksiz veya eksik adımları ve daha uygun çözüm yaklaşımını soru bazında değerlendirir.</div></div>
 <div class="modal-actions"><button class="btn primary" onclick="submitHomeworkAnalysis(${id})">Dosyayı Tara</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
}
function fileToBase64(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(",")[1]);r.onerror=reject;r.readAsDataURL(file)})}
function assignmentResourceContext(a){if(!a||a.kind!=='PDF Kaynak')return null;const r=db.resources.find(x=>x.id===a.sourceId);if(!r)return null;return {resourceId:r.id,driveFileId:r.driveFileId||null,answerKeyDriveFileId:r.answerKeyDriveFileId||null,questionCount:Number(r.questionCount)||null,course:r.course||a.course,unit:r.unit||'',topic:r.subtopic||r.topic||a.topic,level:r.level||'',title:r.title||a.title}}
function homeworkAnswerKeySourceLabel(source){const labels={manual:'Manuel',external_drive:'Ayrı Drive PDF',embedded_same_page:'Kaynak PDF · aynı sayfa',embedded_adjacent_page:'Kaynak PDF · sonraki sayfa',embedded_end_pages:'Kaynak PDF · son sayfalar',ambiguous:'Belirsiz',none:'Bulunamadı'};return labels[String(source||'none')]||String(source||'Bulunamadı')}
window.toggleHomeworkSource=()=>{const src=q("homeworkSource")?.value||"local";const l=q("homeworkLocalWrap"),d=q("homeworkDriveWrap");if(l)l.style.display=src==="local"?"":"none";if(d)d.style.display=src==="drive"?"":"none"}
function driveFileIdFromInput(v){const s=String(v||'').trim();if(!s)return null;const m=s.match(/\/d\/([A-Za-z0-9_-]{10,})/)||s.match(/[?&]id=([A-Za-z0-9_-]{10,})/);return m?m[1]:(/^[A-Za-z0-9_-]{10,}$/.test(s)?s:null)}
async function createHomeworkPdfReport(a,analysis,cost){return await apiJson('/api/reports/homework-pdf',{student:{name:studentName(a.studentId),grade:db.students.find(s=>s.id===a.studentId)?.grade||''},assignment:{title:a.title,course:a.course,topic:a.topic,date:new Date().toISOString().slice(0,10)},analysis,costTry:Number(cost?.try||0)})}
window.lastHomeworkPdfUrl=null;
window.openLastHomeworkPdf=()=>{if(window.lastHomeworkPdfUrl)return window.open(window.lastHomeworkPdfUrl,"_blank");alert("PDF karne oluşturulamadı. Analiz sonucu kaydedildi.")}
window.submitHomeworkAnalysis=async id=>{
 const a=db.assignments.find(x=>x.id===id),studentFileSource=q("homeworkSource")?.value||"local",file=q("homeworkFile")?.files?.[0],studentDriveFileId=driveFileIdFromInput(q("homeworkDriveInput")?.value);if(!a)return;
 if(studentFileSource==="local"&&!file)return alert("Ödev dosyasını seçin");
 if(studentFileSource==="drive"&&!studentDriveFileId)return alert("Geçerli Drive dosya bağlantısı veya kimliği girin");
 if(file&&file.size>14*1024*1024)return alert("Bu sürümde dosya en fazla 14 MB olabilir.");
 const btn=document.querySelector(".modal-actions .btn.primary");if(btn){btn.disabled=true;btn.textContent="AI tarıyor…"}
 try{
  const fileData=studentFileSource==="local"?await fileToBase64(file):null,answerKey=q("answerKey").value.trim()||null,rawContext=assignmentResourceContext(a),resourceContext=rawContext?{resourceId:rawContext.resourceId,course:rawContext.course,unit:rawContext.unit,topic:rawContext.topic,level:rawContext.level,title:rawContext.title}:null;
  const data=await apiJson("/api/ai/analyze-homework",{studentFileSource,studentDriveFileId,fileData,mimeType:file?.type||"application/pdf",fileName:file?.name||"drive_odev.pdf",assignment:{id:a.id,studentId:a.studentId,course:a.course,topic:a.topic,title:a.title},answerKey,resourceContext});
  const an=data.analysis||{},score=Math.round(Number(an.scorePercent)||0),reviewRequired=!!an.needsTeacherReview||data.autoFinalize===false;
  let pdfReport=null;try{pdfReport=await createHomeworkPdfReport(a,an,data.cost)}catch(pdfError){console.warn("PDF_KARNE_ERROR",pdfError.message)}
  window.lastHomeworkPdfUrl=pdfReport?.downloadUrl||null;
  db.homeworkAnalyses.push({id:Date.now(),assignmentId:a.id,studentId:a.studentId,course:a.course,topic:a.topic,date:new Date().toISOString().slice(0,10),fileName:file?.name||"Drive ödevi",fileSize:file?.size||0,mimeType:file?.type||"application/pdf",studentFileSource,costTry:Number(data.cost?.try||0),pdfReportUrl:pdfReport?.downloadUrl||null,...an});
  a.completedAt=new Date().toISOString().slice(0,10);a.score=score;a.aiConfidence=Number(an.confidence||0);
  if(reviewRequired){
    a.status="Öğretmen Kontrolü";
  }else{
    a.status="Tamamlandı";
    db.results.push({id:Date.now()+1,studentId:a.studentId,kind:"AI Ödev Analizi",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});
    if(score<db.threshold&&!db.repeatSignals.some(r=>r.assignmentId===a.id&&r.status==="Bekliyor"))db.repeatSignals.push({id:Date.now()+2,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString()});
  }
  save();
  q("modalbg").querySelector(".modal").innerHTML=`<h2>${reviewRequired?"Öğretmen Kontrolü Gerekli":"Ödev Analizi Tamamlandı"}</h2><div class="result-hero"><div class="kpi">%${score}</div><div><div class="cell-title">${an.correct||0} doğru · ${an.wrong||0} yanlış · ${an.blank||0} boş</div><div class="cell-sub">Güven: %${Math.round((Number(an.confidence)||0)*100)} · Cevap anahtarı: ${homeworkAnswerKeySourceLabel(an.answerKeySource)} (%${Math.round((Number(an.answerKeyConfidence)||0)*100)})${data.cost?` · AI maliyeti ${Number(data.cost.try||0).toFixed(4)} TL`:""}</div></div></div>
   ${reviewRequired?`<div class="notice error"><div><b>Otomatik sonuç kesinleştirilmedi</b>${an.reviewReasons?.length?`Kontrol nedenleri: ${an.reviewReasons.join(", ")}. `:""}Bu analiz başarı sonuçlarına ve tekrar motoruna otomatik aktarılmadı. Atamalar ekranından “Manuel sonuç” ile öğretmen onayı verin.</div></div>`:`<div class="notice"><div><b>${score<db.threshold?"Tekrar sinyali oluşturuldu":"Başarı yeterli"}</b>${score<db.threshold?`%${db.threshold} eşiğinin altında olduğu için ${a.topic} konusu sonraki programda tekrar önceliği alacak.`:"Konu için otomatik tekrar sinyali oluşturulmadı."}</div></div>`}
   <div class="section"><h3>Luna Analiz Mimarisi</h3><div class="cell-sub">${an.analysisArchitecture==="direct_luna_vision"?"PDF doğrudan Luna Vision tarafından analiz edildi":"—"}</div></div>
   <div class="section"><h3>Sayfa Kapsamı</h3><div class="cell-sub">Taranan öğrenci sayfaları: ${(an.analyzedStudentPages||[]).join(", ")||"—"} / beklenen ${an.expectedStudentPages||"?"}${an.missingStudentPages?.length?` · Eksik: ${an.missingStudentPages.join(", ")}`:""}</div></div>
   <div class="section"><h3>Cevap Anahtarı Kanıtı</h3><div class="cell-sub">${an.answerKeyEvidence||"—"}</div></div>
   <div class="section"><h3>Yanlış Soruların Ayrıntılı Analizi</h3>${(an.items||[]).map(x=>'<div class="card" style="margin:8px 0"><div class="cell-title">Soru '+(x.question||"?")+' · '+(x.status||"uncertain")+'</div><div class="cell-sub">Yaklaşım: '+(x.approach||"—")+'<br>İlk hata: '+(x.firstErrorStep||"—")+'<br>Hata sınıfı: '+(x.errorCategory||"—")+'<br>Daha iyi yaklaşım: '+(x.betterApproach||"—")+'<br>Kazanım: '+(x.learningObjective||"—")+'</div></div>').join("")||"—"}</div>
   <div class="section"><h3>Pedagojik Karne</h3><div class="cell-sub"><b>Özet:</b> ${an.reasoningProfile?.summary||an.summary||"—"}<br><br><b>Güçlü yönler:</b> ${(an.reasoningProfile?.strengths||[]).join(", ")||"—"}<br><b>Tekrarlayan hatalar:</b> ${(an.reasoningProfile?.recurringErrors||[]).join(", ")||"—"}<br><b>Kavramsal eksikler:</b> ${(an.reasoningProfile?.conceptualGaps||[]).join(", ")||"—"}<br><b>İşlem/prosedür eksikleri:</b> ${(an.reasoningProfile?.proceduralGaps||[]).join(", ")||"—"}<br><b>Dikkat örüntüleri:</b> ${(an.reasoningProfile?.attentionPatterns||[]).join(", ")||"—"}<br><b>Önerilen çalışma:</b> ${(an.reasoningProfile?.recommendedActions||[]).join(", ")||"—"}</div></div>
   <div class="section"><h3>Zayıf Alanlar</h3>${(an.weaknesses||[]).map(x=>`<span class="course-chip">${x}</span>`).join("")||"—"}</div>
   <div class="section"><h3>Hata Türleri</h3>${(an.errorTypes||[]).map(x=>`<span class="course-chip">${typeof x==="string"?x:(x.type||x.label||JSON.stringify(x))}</span>`).join("")||"—"}</div>
   <div class="notice"><div><b>PDF Karne</b>Analiz tamamlandığında PDF karne yerel olarak hazırlanır; ek AI maliyeti yoktur.</div></div><div class="modal-actions"><button class="btn primary" onclick="openLastHomeworkPdf()">PDF Karnesini İndir</button><button class="btn ghost" onclick="closeModal();assignments()">Tamam</button></div>`;
 }catch(e){alert("Ödev analizi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent="Dosyayı Tara"}}
}

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.11.1 */

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.7.2 */
function q(id){return document.getElementById(id)}
function modal(html){const d=document.createElement("div");d.className="modalbg";d.id="modalbg";d.innerHTML=`<div class="modal">${html}</div>`;document.body.appendChild(d)}
window.closeModal=()=>document.getElementById("modalbg")?.remove()
window.resetDemo=()=>{db=structuredClone(seed);save();render()}

/* CELL:bootstrap */

/* CELL:bootstrap */

async function loadDriveStatus(){const el=q("drivePanel");if(!el)return;try{const d=await apiJson("/api/drive/status");el.innerHTML=`<div class="integration-grid"><div class="card integration-card"><div class="integration-head"><div><div class="cell-title">Google Drive</div><div class="cell-sub">PDF kaynak havuzu · drive.readonly</div></div><span class="badge ${d.connected?"good":d.configured?"mid":"neutral"}">${d.connected?"Bağlı":d.configured?"Yetkilendirme gerekli":"OAuth ayarı gerekli"}</span></div><div class="integration-meta"><div style="margin-bottom:8px"><b>Cevap anahtarı:</b> Kaynak dosya adının sonuna <code>__CEVAP</code> ekleyin.<br><span class="muted">Örn: <code>...__Test 01.pdf</code> → <code>...__Test 01__CEVAP.pdf</code></span></div>Klasör: <b>${d.folderConfigured?"Ayarlı":"Ayarlanmamış"}</b></div><div class="toolbar-group" style="margin-top:12px">${d.configured&&!d.connected?`<button class="btn primary" onclick="connectGoogleDrive()">Google Drive'a Bağlan</button>`:""}${d.connected?`<button class="btn primary" onclick="indexGoogleDrive()">PDF'leri İndeksle</button><button class="btn ghost" onclick="disconnectGoogleDrive()">Bağlantıyı Kes</button>`:""}</div></div></div>`}catch(e){el.innerHTML=`<div class="notice error">Drive durumu okunamadı: ${e.message}</div>`}}
window.connectGoogleDrive=async()=>{try{const d=await apiJson("/api/drive/oauth/start",{});window.open(d.authorizationUrl,"_blank","noopener");alert("Google yetkilendirme ekranı açıldı. Onaydan sonra bu sayfaya dönün.");setTimeout(loadDriveStatus,2500)}catch(e){alert("Drive bağlantısı başlatılamadı: "+e.message)}}
window.disconnectGoogleDrive=async()=>{if(!confirm("Google Drive bağlantısı kesilsin mi?"))return;try{await apiJson("/api/drive/disconnect",{});loadDriveStatus()}catch(e){alert("Drive bağlantısı kesilemedi: "+e.message)}}
function upsertDriveResource(x,newId){const matches=db.resources.map((r,i)=>({r,i})).filter(z=>z.r.driveFileId===x.id);const existing=matches[0]?.r||null;const next={type:'PDF',course:x.course,topic:x.topic,unit:x.unit||existing?.unit||'',subtopic:x.subtopic||existing?.subtopic||x.topic,level:x.level,title:x.title||x.name,questionCount:Number(x.questionCount)>0?Number(x.questionCount):(Number(existing?.questionCount)||0),answerKeyDriveFileId:x.answerKeyDriveFileId||existing?.answerKeyDriveFileId||'',url:x.webViewLink||'',driveFileId:x.id,driveModifiedTime:x.modifiedTime||null,driveSource:true};if(existing){Object.assign(existing,next);for(let i=matches.length-1;i>=1;i--)db.resources.splice(matches[i].i,1);return 'updated'}db.resources.push({id:newId,...next});return 'added'}
window.indexGoogleDrive=async()=>{try{const d=await apiJson("/api/drive/index",{});let added=0,updated=0;for(const x of d.items||[]){if(!x.matched)continue;const result=upsertDriveResource(x,Date.now()+added);if(result==="added")added++;else if(result==="updated")updated++}save();loadDriveStatus();alert(`Drive indeksleme tamamlandı.\nEşleşen: ${d.matchedCount||0}\nMetadata gerekli: ${d.unmatchedCount||0}\nYeni kaynak: ${added}\nGüncellenen: ${updated}\nCevap anahtarı: ${d.answerKeyCount||0}\nOtomatik eşleşen cevap anahtarı: ${d.pairedAnswerKeyCount||0}\nBelirsiz eşleşme: ${d.ambiguousAnswerKeyCount||0}`)}catch(e){alert("Drive indeksleme başarısız: "+e.message)}}

function applyViewportProfile(){const w=Math.max(0,Math.round(window.innerWidth||document.documentElement.clientWidth||0)),h=Math.max(0,Math.round(window.innerHeight||document.documentElement.clientHeight||0)),dpr=Math.max(1,Number(window.devicePixelRatio)||1),root=document.documentElement;let density='normal';if(w<900)density='narrow';else if(h<800||w<1400)density='compact';root.dataset.uiDensity=density;root.style.setProperty('--viewport-w',w+'px');root.style.setProperty('--viewport-h',h+'px');root.style.setProperty('--device-scale',String(dpr));return {width:w,height:h,dpr,density}}
window.addEventListener('resize',applyViewportProfile,{passive:true})
applyViewportProfile()
dashboard();

/* UI regression marker: İşlenen / Taranmış PDF'ler | Taranmış PDF kaydını sil | deleteHomeworkAnalysis */
