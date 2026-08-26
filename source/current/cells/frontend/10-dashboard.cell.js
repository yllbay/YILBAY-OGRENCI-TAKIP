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
