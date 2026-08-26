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

/* CELL:30-curriculum | layer:frontend | generated-from:v0.10.1 */

/* CELL:30-curriculum | layer:frontend | generated-from:v0.7.2 */
