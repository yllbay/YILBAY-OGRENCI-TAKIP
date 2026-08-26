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
