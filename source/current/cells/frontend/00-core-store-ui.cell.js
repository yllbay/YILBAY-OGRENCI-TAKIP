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
function shell(content,active=view){app().innerHTML=`<div class="top"><div class="brand-wrap"><div class="brandmark">Y</div><div><div class="brand">YILBAY Öğrenci Takip</div><div class="brand-sub">Akademik Koçluk Yönetim Sistemi</div></div></div><div class="top-right"><span class="version">v0.8.0</span></div></div><div class="layout"><aside>
<div class="nav-section">Yönetim</div>${nav("dashboard","Genel Bakış",active)}${nav("students","Öğrenciler",active)}${nav("profile","Öğrenci Profili",active)}
<div class="nav-section">Akademik İçerik</div>${nav("curriculum","Ders ve Üniteler",active)}${nav("resources","Kaynak Havuzu",active)}${nav("exams","Online Sınavlar",active)}
<div class="nav-section">Operasyon</div>${nav("assignments","Atamalar",active)}${nav("results","Başarı Sonuçları",active)}${nav("program","Haftalık Program",active)}
<div class="nav-section">Sistem</div>${nav("integrations","AI ve API Entegrasyonları",active)}
</aside><main><div class="page">${content}</div></main></div>`}
function nav(k,t,a){return `<button class="nav ${a===k?"active":""}" onclick="go('${k}')">${t}</button>`}
window.go=k=>{view=k;render()}
function render(){({dashboard,students,profile,curriculum,resources,exams,assignments,results,program,integrations}[view]||dashboard)()}
