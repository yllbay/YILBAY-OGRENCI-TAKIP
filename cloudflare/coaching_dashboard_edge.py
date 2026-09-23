from pathlib import Path

p=Path("cloudflare/package-runtime/index.js")
src=p.read_text(encoding="utf-8")
MARK="GENESIS_COACHING_DASHBOARD_EDGE_V1"
if MARK in src:
    print("coaching dashboard edge overlay already present")
    raise SystemExit(0)

needle='''      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers
      });'''

overlay=r'''
      // GENESIS_COACHING_DASHBOARD_EDGE_V1
      if (request.method === "GET" && url.pathname === "/coaching" && contentType.includes("text/html")) {
        let html = await upstream.text();
        if (!html.includes("GENESIS_COACHING_DASHBOARD_EDGE_V1")) {
          const coachingOverlay = String.raw`
<style id="genesisCoachingDashboardEdgeStyle">
/* GENESIS_COACHING_DASHBOARD_EDGE_V1 */
:root{--gcd-bg:#081426;--gcd-panel:#0d1b31;--gcd-panel2:#111f38;--gcd-line:#29405f;--gcd-text:#eef3ff;--gcd-muted:#93a4c3;--gcd-purple:#7c3cff;--gcd-purple2:#a16cff;--gcd-blue:#4ea7ff;--gcd-green:#34d399;--gcd-yellow:#f3ba3e;--gcd-red:#f0647f}
#coachApp.genesis-coaching-dashboard-mode>.layout,#coachApp.genesis-coaching-dashboard-mode>.mobile-nav{display:none!important}
#coachApp.genesis-coaching-dashboard-mode>.top .top-right>.status,
#coachApp.genesis-coaching-dashboard-mode>.top .top-right>a{display:none!important}
#coachApp.genesis-coaching-dashboard-mode>.top{border-bottom:1px solid #263b5b}
#genesisCoachingDashboardV1{box-sizing:border-box;min-height:calc(100vh - 72px);padding:14px;background:radial-gradient(circle at 55% -10%,#213c694d,transparent 38%),var(--gcd-bg);color:var(--gcd-text)}
.gcd-grid{display:grid;grid-template-columns:minmax(250px,310px) minmax(520px,1fr) minmax(250px,330px);gap:14px;align-items:stretch;min-height:calc(100vh - 100px)}
.gcd-panel{min-width:0;background:linear-gradient(180deg,#0e1c33,#0a172a);border:1px solid var(--gcd-line);border-radius:17px;overflow:hidden;box-shadow:0 18px 45px #02081738}
.gcd-panel-head{min-height:72px;padding:15px 17px;display:flex;align-items:center;justify-content:space-between;gap:12px;background:linear-gradient(115deg,#5c27b6,#8142d6 62%,#7154df);border-bottom:1px solid #7659b8}
.gcd-panel-head h2{margin:0;font-size:18px;line-height:1.15}.gcd-panel-head p{margin:5px 0 0;color:#e3d9ff;font-size:11px}.gcd-panel-body{padding:14px}
.gcd-search{display:flex;align-items:center;gap:9px;height:42px;padding:0 12px;border:1px solid #334b70;border-radius:11px;background:#0a1729}.gcd-search input{width:100%;border:0;outline:0;background:transparent;color:var(--gcd-text);font:inherit}.gcd-search input::placeholder{color:#7284a5}
.gcd-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.gcd-btn,.gcd-action-row,.gcd-tab,.gcd-nav-btn{border:1px solid #344c73;background:#11213a;color:var(--gcd-text);border-radius:10px;font:inherit;cursor:pointer}.gcd-btn{min-height:42px;padding:0 11px;font-weight:750}.gcd-btn.primary{background:linear-gradient(135deg,#6f36d9,#7e52e7);border-color:#9b79ff}.gcd-btn:hover,.gcd-action-row:hover,.gcd-nav-btn:hover{border-color:#765cc1;background:#172946}.gcd-btn:disabled{opacity:.48;cursor:not-allowed}
.gcd-section-title{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:16px 0 8px;color:#c9d5eb;font-size:11px;font-weight:800;letter-spacing:.35px;text-transform:uppercase}
.gcd-student-list{display:grid;gap:7px;max-height:45vh;overflow:auto;padding-right:2px}.gcd-student{display:grid;grid-template-columns:38px minmax(0,1fr) 20px;gap:9px;align-items:center;width:100%;padding:9px;border:1px solid #273c5d;border-radius:11px;background:#0e1c32;color:var(--gcd-text);text-align:left;cursor:pointer}.gcd-student.on{border-color:#865cf0;background:linear-gradient(135deg,#2b2450,#17243d)}.gcd-avatar{width:36px;height:36px;display:grid;place-items:center;border-radius:10px;background:linear-gradient(135deg,#7342e8,#4d6ce8);font-size:12px;font-weight:900}.gcd-student b{display:block;font-size:12px}.gcd-student small{display:block;margin-top:3px;color:var(--gcd-muted);font-size:10px}.gcd-empty{padding:18px 10px;color:var(--gcd-muted);font-size:11px;text-align:center}
.gcd-selected{margin-top:12px;padding:11px;border:1px solid #30486c;border-radius:12px;background:#10203a}.gcd-selected b{display:block;font-size:13px}.gcd-selected small{display:block;margin-top:4px;color:var(--gcd-muted);font-size:10px}
.gcd-center-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.gcd-tabs{display:flex;gap:4px;padding:4px;border-radius:11px;background:#3f237a99}.gcd-tab{border:0;min-height:34px;padding:0 14px;background:transparent;font-size:11px;font-weight:800}.gcd-tab.on{background:#8a5cf3;box-shadow:0 3px 12px #28155066}
.gcd-toolbar{display:flex;align-items:center;justify-content:center;gap:9px;padding:12px 14px;border-bottom:1px solid #213858}.gcd-toolbar strong{min-width:160px;text-align:center;font-size:12px}.gcd-nav-btn{width:36px;height:34px;font-weight:900}
.gcd-week{display:grid;grid-template-columns:repeat(7,minmax(105px,1fr));gap:8px;padding:12px;overflow-x:auto}.gcd-day{min-width:105px;border:1px solid #29405f;border-radius:12px;background:#0b192d;overflow:hidden}.gcd-day-head{padding:10px;border-top:3px solid #7a4ee7;border-bottom:1px solid #273e5d}.gcd-day-head b{display:block;font-size:11px}.gcd-day-head span{display:block;margin-top:2px;color:var(--gcd-muted);font-size:9px}.gcd-day-body{display:grid;gap:7px;padding:8px;min-height:340px}.gcd-task{padding:8px;border:1px solid #243b5a;border-radius:9px;background:#11213a}.gcd-task b{display:block;font-size:10px;line-height:1.3}.gcd-task small{display:block;margin-top:4px;color:var(--gcd-muted);font-size:9px;line-height:1.35}.gcd-task-meta{display:flex;justify-content:space-between;gap:6px;margin-top:7px;color:#8da0c2;font-size:8px}.gcd-task.done{border-color:#2e7c69}.gcd-exam{border-color:#4a4291}.gcd-badge{display:inline-flex;align-items:center;justify-content:center;min-height:20px;padding:0 7px;border-radius:999px;background:#213653;color:#c9d6ed;font-size:8px;font-weight:800}.gcd-badge.done{background:#164b40;color:#84f0c6}.gcd-badge.exam{background:#312861;color:#c8b9ff}
.gcd-today,.gcd-history{padding:14px;display:grid;gap:9px}.gcd-list-row{display:grid;grid-template-columns:62px minmax(0,1fr) auto;gap:11px;align-items:center;padding:11px;border:1px solid #29405f;border-radius:11px;background:#0d1b31}.gcd-list-row time{color:#91a4c6;font-size:10px}.gcd-list-row b{display:block;font-size:11px}.gcd-list-row small{display:block;margin-top:4px;color:var(--gcd-muted);font-size:9px}
.gcd-right-stack{display:grid;gap:12px}.gcd-mini{border:1px solid #2a4162;border-radius:13px;background:#0d1b31;overflow:hidden}.gcd-mini h3{margin:0;padding:12px 14px;background:linear-gradient(110deg,#4e2498,#7240c7);font-size:13px}.gcd-mini-body{padding:10px}.gcd-action-row{width:100%;display:grid;grid-template-columns:30px minmax(0,1fr) 18px;align-items:center;gap:8px;min-height:48px;padding:8px 10px;margin-bottom:7px;text-align:left}.gcd-action-row span:first-child{width:28px;height:28px;display:grid;place-items:center;border-radius:8px;background:#1a3151;color:#b9c9e6}.gcd-action-row b{display:block;font-size:10px}.gcd-action-row small{display:block;margin-top:3px;color:var(--gcd-muted);font-size:8.5px}.gcd-action-row:last-child{margin-bottom:0}
.gcd-summary{display:grid;grid-template-columns:1fr 1fr;gap:8px}.gcd-stat{padding:10px;border:1px solid #2a4162;border-radius:10px;background:#102039}.gcd-stat small{display:block;color:var(--gcd-muted);font-size:8px}.gcd-stat strong{display:block;margin-top:5px;font-size:18px}.gcd-note{margin-top:10px;padding:9px 10px;border:1px solid #5b4a2f;border-radius:10px;background:#2b2417;color:#e8c980;font-size:9px;line-height:1.4}
#gcdNotice{position:fixed;left:50%;bottom:22px;z-index:9999;transform:translateX(-50%) translateY(20px);opacity:0;pointer-events:none;padding:10px 14px;border:1px solid #5a4a8b;border-radius:10px;background:#151d33;color:#eef3ff;font-size:11px;box-shadow:0 18px 50px #0008;transition:.18s}#gcdNotice.show{opacity:1;transform:translateX(-50%) translateY(0)}
#genesisCoachingBackDashboard{position:fixed;right:18px;bottom:18px;z-index:9998;display:none;min-height:42px;padding:0 14px;border:1px solid #8d68e8;border-radius:11px;background:#5e34bc;color:white;font:inherit;font-size:11px;font-weight:800;cursor:pointer}
#coachApp.genesis-coaching-workspace-mode #genesisCoachingDashboardV1{display:none!important}#coachApp.genesis-coaching-workspace-mode>.layout{display:grid!important}#coachApp.genesis-coaching-workspace-mode #genesisCoachingBackDashboard{display:block}
@media(max-width:1180px){.gcd-grid{grid-template-columns:250px minmax(480px,1fr)}.gcd-right{grid-column:1/-1}.gcd-right-stack{grid-template-columns:1fr 1fr 1fr}}
@media(max-width:820px){#genesisCoachingDashboardV1{padding:8px}.gcd-grid{grid-template-columns:1fr;min-height:auto}.gcd-left,.gcd-center,.gcd-right{grid-column:auto}.gcd-right-stack{grid-template-columns:1fr}.gcd-week{grid-template-columns:repeat(7,150px)}.gcd-student-list{max-height:260px}.gcd-panel-head{min-height:64px}.gcd-center-head{flex-direction:column}.gcd-tabs{width:100%}.gcd-tab{flex:1}}
</style>
<script id="genesisCoachingDashboardEdgeScript">
/* GENESIS_COACHING_DASHBOARD_EDGE_V1 */
(function(){
  var S={students:[],selected:null,dashboard:null,view:"week",week:null,loading:false};
  var dayNames=["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"];
  function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]})}
  function iso(d){var x=new Date(d.getTime()-d.getTimezoneOffset()*60000);return x.toISOString().slice(0,10)}
  function monday(v){var d=v?new Date(v+"T12:00:00"):new Date(),n=d.getDay();d.setDate(d.getDate()-(n===0?6:n-1));return iso(d)}
  function plus(v,n){var d=new Date(v+"T12:00:00");d.setDate(d.getDate()+n);return iso(d)}
  function fmt(v){if(!v)return "";return new Intl.DateTimeFormat("tr-TR",{day:"2-digit",month:"short"}).format(new Date(v+"T12:00:00"))}
  function selectedStudent(){for(var i=0;i<S.students.length;i++)if(Number(S.students[i].id)===Number(S.selected))return S.students[i];return null}
  function notice(msg){var n=document.getElementById("gcdNotice");if(!n)return;n.textContent=msg;n.classList.add("show");clearTimeout(notice.t);notice.t=setTimeout(function(){n.classList.remove("show")},2600)}
  async function api(path){var r=await fetch(path,{credentials:"same-origin",headers:{"Accept":"application/json"}});var text=await r.text();if(!r.ok)throw new Error(text||("HTTP "+r.status));return text?JSON.parse(text):{}}
  function bridgeClick(sel){var el=document.querySelector(sel);if(el){el.click();return true}return false}
  function legacyStudentClick(id){var b=document.querySelector('#studentList [data-student="'+id+'"]');if(b)b.click()}
  function openWorkspace(tab){var app=document.getElementById("coachApp");if(!app)return;app.classList.remove("genesis-coaching-dashboard-mode");app.classList.add("genesis-coaching-workspace-mode");setTimeout(function(){if(tab)bridgeClick('[data-tab="'+tab+'"]')},40)}
  function backDashboard(){var app=document.getElementById("coachApp");if(!app)return;app.classList.remove("genesis-coaching-workspace-mode");app.classList.add("genesis-coaching-dashboard-mode");syncFromLegacy();renderAll()}
  function taskHtml(t){var done=String(t.status||"").toUpperCase()==="DONE";return '<div class="gcd-task '+(done?'done':'')+'"><b>'+esc(t.course_name||"Çalışma")+'</b><small>'+esc(t.topic_name||t.note||"Çalışma görevi")+'</small><div class="gcd-task-meta"><span>'+esc((t.minutes||0)+" dk")+'</span><span class="gcd-badge '+(done?'done':'')+'">'+(done?"Tamamlandı":"Planlandı")+'</span></div></div>'}
  function examHtml(a){return '<div class="gcd-task gcd-exam"><b>'+esc(a.course_name||"Online Sınav")+'</b><small>'+esc(a.source_exam_name||"Online sınav")+'</small><div class="gcd-task-meta"><span>'+esc((a.duration_minutes||0)+" dk")+'</span><span class="gcd-badge exam">Sınav</span></div></div>'}
  function listRow(kind,x){var title=kind==="exam"?(x.course_name||"Online Sınav"):(x.course_name||"Çalışma");var sub=kind==="exam"?(x.source_exam_name||"Online sınav"):(x.topic_name||x.note||"Çalışma görevi");var date=kind==="exam"?x.exam_date:x.plan_date;return '<div class="gcd-list-row"><time>'+esc(fmt(date))+'</time><div><b>'+esc(title)+'</b><small>'+esc(sub)+'</small></div><span class="gcd-badge '+(kind==="exam"?'exam':'')+'">'+(kind==="exam"?"Sınav":esc((x.minutes||0)+" dk"))+'</span></div>'}
  function renderStudents(){
    var host=document.getElementById("gcdStudentList");if(!host)return;
    var q=(document.getElementById("gcdSearch")||{}).value||"";q=q.toLocaleLowerCase("tr-TR");
    var xs=S.students.filter(function(s){return ((s.name||"")+" "+(s.number||"")).toLocaleLowerCase("tr-TR").indexOf(q)>=0});
    host.innerHTML=xs.map(function(s){return '<button class="gcd-student '+(Number(s.id)===Number(S.selected)?'on':'')+'" data-gcd-student="'+s.id+'"><span class="gcd-avatar">'+esc((s.name||"?").slice(0,1).toUpperCase())+'</span><span><b>'+esc(s.name||"Öğrenci")+'</b><small>'+esc(s.number||"Numarasız")+' • '+esc((s.course_count||0)+" ders")+'</small></span><span>›</span></button>'}).join("")||'<div class="gcd-empty">Öğrenci bulunamadı.</div>';
    var sel=selectedStudent(),card=document.getElementById("gcdSelected");
    if(card)card.innerHTML=sel?'<b>'+esc(sel.name)+'</b><small>'+esc((sel.number||"Numarasız")+" • "+(sel.course_count||0)+" atanmış ders")+'</small>':'<b>Öğrenci seçilmedi</b><small>Haftalık plan için bir öğrenci seçin.</small>';
  }
  function renderSummary(){
    var d=S.dashboard,sm=d&&d.summary?d.summary:{courses:0,tasks:0,done:0,minutes:0,exams:0};
    var h=document.getElementById("gcdSummary");if(h)h.innerHTML='<div class="gcd-stat"><small>Atanan Ders</small><strong>'+esc(sm.courses||0)+'</strong></div><div class="gcd-stat"><small>Haftalık Görev</small><strong>'+esc(sm.tasks||0)+'</strong></div><div class="gcd-stat"><small>Tamamlanan</small><strong>'+esc(sm.done||0)+'</strong></div><div class="gcd-stat"><small>Online Sınav</small><strong>'+esc(sm.exams||0)+'</strong></div>';
    var lvl=document.getElementById("gcdLevelInfo");if(lvl)lvl.textContent="Düzey kuralı henüz veri modeline bağlanmadı.";
  }
  function renderWeek(){
    var host=document.getElementById("gcdPlanner");if(!host)return;
    if(!S.dashboard){host.innerHTML='<div class="gcd-empty">Haftalık planı görmek için bir öğrenci seçin.</div>';return}
    var tasks=S.dashboard.tasks||[],exams=S.dashboard.assignments||[];
    var html='<div class="gcd-week">';
    for(var i=0;i<7;i++){var date=plus(S.week,i),ts=tasks.filter(function(t){return t.plan_date===date}),es=exams.filter(function(a){return a.exam_date===date});
      html+='<section class="gcd-day"><div class="gcd-day-head"><b>'+dayNames[i]+'</b><span>'+fmt(date)+'</span></div><div class="gcd-day-body">'+ts.map(taskHtml).join("")+es.map(examHtml).join("")+((!ts.length&&!es.length)?'<div class="gcd-empty">Görev yok</div>':'')+'</div></section>'}
    host.innerHTML=html+'</div>';
  }
  function renderToday(){
    var host=document.getElementById("gcdPlanner");if(!host)return;
    if(!S.dashboard){host.innerHTML='<div class="gcd-empty">Bugünün planını görmek için bir öğrenci seçin.</div>';return}
    var date=iso(new Date()),tasks=(S.dashboard.tasks||[]).filter(function(t){return t.plan_date===date}),exams=(S.dashboard.assignments||[]).filter(function(a){return a.exam_date===date});
    host.innerHTML='<div class="gcd-today">'+tasks.map(function(t){return listRow("task",t)}).join("")+exams.map(function(a){return listRow("exam",a)}).join("")+((!tasks.length&&!exams.length)?'<div class="gcd-empty">Bugün için planlanmış görev bulunmuyor.</div>':'')+'</div>';
  }
  function renderHistory(){
    var host=document.getElementById("gcdPlanner");if(!host)return;
    if(!S.dashboard){host.innerHTML='<div class="gcd-empty">Geçmiş ödevleri görmek için bir öğrenci seçin.</div>';return}
    var today=iso(new Date()),tasks=(S.dashboard.tasks||[]).filter(function(t){return t.plan_date<today||String(t.status||"").toUpperCase()==="DONE"});
    host.innerHTML='<div class="gcd-history">'+tasks.map(function(t){return listRow("task",t)}).join("")+(tasks.length?'':'<div class="gcd-empty">Bu hafta için geçmiş/tamamlanmış ödev bulunmuyor.</div>')+'</div>';
  }
  function renderPlanner(){
    document.querySelectorAll("[data-gcd-view]").forEach(function(b){b.classList.toggle("on",b.getAttribute("data-gcd-view")===S.view)});
    var range=document.getElementById("gcdWeekRange");if(range)range.textContent=fmt(S.week)+" – "+fmt(plus(S.week,6));
    if(S.view==="today")renderToday();else if(S.view==="history")renderHistory();else renderWeek();
  }
  function renderAll(){renderStudents();renderSummary();renderPlanner()}
  async function loadStudents(){
    S.loading=true;try{var x=await api("/api/coaching/v2/students");S.students=x.students||[];var legacy=document.querySelector("#studentList .student-item.on");var lid=legacy&&legacy.getAttribute("data-student");if(lid)S.selected=Number(lid);if(!S.selected&&S.students.length)S.selected=Number(S.students[0].id);if(S.selected)await loadDashboard(S.selected);else renderAll()}catch(e){notice("Koçluk verisi yüklenemedi.");renderAll()}finally{S.loading=false}
  }
  async function loadDashboard(id){S.selected=Number(id);legacyStudentClick(id);try{S.dashboard=await api("/api/coaching/v2/students/"+id+"/dashboard?week_start="+encodeURIComponent(S.week));renderAll()}catch(e){S.dashboard=null;renderAll();notice("Öğrenci planı yüklenemedi.")}}
  function syncFromLegacy(){var legacy=document.querySelector("#studentList .student-item.on");var id=legacy&&legacy.getAttribute("data-student");if(id&&Number(id)!==Number(S.selected)){S.selected=Number(id);loadDashboard(S.selected)}}
  function shell(){
    return '<div class="gcd-grid"><section class="gcd-panel gcd-left"><header class="gcd-panel-head"><div><h2>Sınıflar ve Öğrenciler</h2><p>Sınıf ve öğrenci çalışma alanı</p></div><span>◉</span></header><div class="gcd-panel-body"><label class="gcd-search"><span>⌕</span><input id="gcdSearch" placeholder="Öğrenci ara" autocomplete="off"></label><div class="gcd-actions"><button class="gcd-btn" id="gcdAddClass">+ Sınıf</button><button class="gcd-btn primary" id="gcdAddStudent">+ Öğrenci</button></div><div class="gcd-section-title"><span>Öğrenciler</span><span id="gcdStudentCount">0</span></div><div id="gcdStudentList" class="gcd-student-list"></div><div class="gcd-section-title">Seçili Öğrenci</div><div id="gcdSelected" class="gcd-selected"></div><div class="gcd-actions"><button class="gcd-btn" id="gcdAssignCourse">Ders Ata</button><button class="gcd-btn" id="gcdStudentDetail">Detay</button></div></div></section><section class="gcd-panel gcd-center"><header class="gcd-panel-head"><div class="gcd-center-head"><div><h2>Haftalık Çalışma Programı</h2><p>Görevler ve sınavlar tek görünümde</p></div></div><div class="gcd-tabs"><button class="gcd-tab" data-gcd-view="today">Bugün</button><button class="gcd-tab on" data-gcd-view="week">Hafta</button><button class="gcd-tab" data-gcd-view="history">Geçmiş Ödevler</button></div></header><div class="gcd-toolbar"><button class="gcd-nav-btn" id="gcdPrevWeek">‹</button><strong id="gcdWeekRange"></strong><button class="gcd-nav-btn" id="gcdNextWeek">›</button><button class="gcd-btn" id="gcdThisWeek">Bu Hafta</button></div><div id="gcdPlanner"></div></section><aside class="gcd-right"><div class="gcd-panel"><header class="gcd-panel-head"><div><h2>Akademik Yapı ve Atamalar</h2><p>Ders, konu, sorumluluk ve içerik</p></div><span>▰</span></header><div class="gcd-panel-body gcd-right-stack"><section class="gcd-mini"><h3>Akademik Yapı</h3><div class="gcd-mini-body"><button class="gcd-action-row" data-gcd-action="courses"><span>▤</span><span><b>Dersler</b><small>Öğrenciye ders ve konu ata</small></span><span>›</span></button><button class="gcd-action-row" data-gcd-action="curriculum"><span>▰</span><span><b>Üniteler ve Alt Başlıklar</b><small>Merkezi müfredat yapısını yönet</small></span><span>›</span></button><button class="gcd-action-row" data-gcd-action="responsibility"><span>✓</span><span><b>Sorumluluk Seçimi</b><small>Çalışılacak konuları belirle</small></span><span>›</span></button><button class="gcd-action-row" data-gcd-action="content"><span>⇧</span><span><b>İçerik Yüklemeleri</b><small>PDF ve test içerik alanı</small></span><span>›</span></button></div></section><section class="gcd-mini"><h3>Otomatik Ödev Ayarı</h3><div class="gcd-mini-body"><div class="gcd-selected"><b>Sınıf / Öğrenci Düzeyi</b><small id="gcdLevelInfo"></small></div><div class="gcd-note">Kolay / Orta / Zor otomatik ödev eşleştirmesi veri modeli eklendiğinde bu alana bağlanacak.</div></div></section><section class="gcd-mini"><h3>Sınav ve Karne</h3><div class="gcd-mini-body"><div id="gcdSummary" class="gcd-summary"></div><div class="gcd-actions"><button class="gcd-btn" data-gcd-action="exams">Sınavlar</button><button class="gcd-btn" data-gcd-action="insights">Karne / Analiz</button></div></div></section></div></div></aside></div>';
  }
  function install(){
    var app=document.getElementById("coachApp"),top=app&&app.querySelector(".top");if(!app||!top)return false;
    if(document.getElementById("genesisCoachingDashboardV1"))return true;
    var dash=document.createElement("div");dash.id="genesisCoachingDashboardV1";dash.innerHTML=shell();top.insertAdjacentElement("afterend",dash);
    var back=document.createElement("button");back.id="genesisCoachingBackDashboard";back.type="button";back.textContent="← Dashboard";app.appendChild(back);
    var n=document.createElement("div");n.id="gcdNotice";app.appendChild(n);
    app.classList.add("genesis-coaching-dashboard-mode");
    S.week=monday();
    document.getElementById("gcdStudentCount").textContent="0";
    dash.addEventListener("click",function(e){
      var b=e.target.closest("button");if(!b)return;
      var sid=b.getAttribute("data-gcd-student");if(sid){loadDashboard(Number(sid));return}
      var view=b.getAttribute("data-gcd-view");if(view){S.view=view;renderPlanner();return}
      var action=b.getAttribute("data-gcd-action");
      if(action==="courses"||action==="responsibility"){if(!S.selected){notice("Önce öğrenci seçin.");return}openWorkspace("courses");return}
      if(action==="curriculum"){location.assign("/static/coaching-curriculum.html");return}
      if(action==="content"){openWorkspace(null);setTimeout(function(){if(!bridgeClick("#addCourseWorkspace"))notice("İçerik çalışma alanı açılamadı.")},60);return}
      if(action==="exams"){if(!S.selected){notice("Önce öğrenci seçin.");return}openWorkspace("exams");return}
      if(action==="insights"){if(!S.selected){notice("Önce öğrenci seçin.");return}openWorkspace("insights");return}
      if(b.id==="gcdAddClass"){notice("Sınıf veri modeli bir sonraki geliştirme adımında bağlanacak.");return}
      if(b.id==="gcdAddStudent"){bridgeClick("#addStudent");return}
      if(b.id==="gcdAssignCourse"){if(!S.selected){notice("Önce öğrenci seçin.");return}openWorkspace("courses");setTimeout(function(){bridgeClick("#newCourse")},100);return}
      if(b.id==="gcdStudentDetail"){if(!S.selected){notice("Önce öğrenci seçin.");return}openWorkspace("overview");return}
      if(b.id==="gcdPrevWeek"){S.week=plus(S.week,-7);if(S.selected)loadDashboard(S.selected);else renderPlanner();return}
      if(b.id==="gcdNextWeek"){S.week=plus(S.week,7);if(S.selected)loadDashboard(S.selected);else renderPlanner();return}
      if(b.id==="gcdThisWeek"){S.week=monday();if(S.selected)loadDashboard(S.selected);else renderPlanner();return}
    });
    dash.addEventListener("input",function(e){if(e.target.id==="gcdSearch")renderStudents()});
    back.addEventListener("click",backDashboard);
    var mo=new MutationObserver(function(){var count=document.querySelectorAll("#studentList .student-item").length;var c=document.getElementById("gcdStudentCount");if(c)c.textContent=String(S.students.length||count);syncFromLegacy()});mo.observe(app,{childList:true,subtree:true});
    loadStudents().then(function(){var c=document.getElementById("gcdStudentCount");if(c)c.textContent=String(S.students.length)});
    return true
  }
  if(!install()){var o=new MutationObserver(function(){if(install())o.disconnect()});o.observe(document.documentElement,{childList:true,subtree:true});setTimeout(function(){o.disconnect()},15000)}
})();
</script>`;
          html = html.includes("</body>") ? html.replace("</body>", coachingOverlay + "</body>") : html + coachingOverlay;
          headers.delete("content-length");
        }
        headers.set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
        return new Response(html, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers
        });
      }
'''

if "GENESIS_HOME_DASHBOARD_EDGE_V1" not in src:
    raise SystemExit("Home dashboard edge marker missing from live Worker")

pos=src.rfind(needle)
if pos<0:
    raise SystemExit("Worker final response patch point not found")
src=src[:pos]+overlay+src[pos:]
p.write_text(src,encoding="utf-8")

out=p.read_text(encoding="utf-8")
assert MARK in out
assert "Sınıflar ve Öğrenciler" in out
assert "Haftalık Çalışma Programı" in out
assert "Akademik Yapı ve Atamalar" in out
assert "/api/coaching/v2/students" in out
assert 'location.assign("/static/coaching-curriculum.html")' in out
assert 'openWorkspace("courses")' in out
assert 'openWorkspace("exams")' in out
assert 'openWorkspace("insights")' in out
print("GENESIS coaching dashboard edge overlay patch: OK")
