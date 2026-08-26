function curriculum(){
 let cards="";for(const [course,units] of Object.entries(db.curriculum)){cards+=`<div class="card"><div class="section-head"><h2 style="margin:0">${course}</h2><span class="badge info">${Object.values(units).reduce((n,x)=>n+x.length,0)} konu</span></div>`;for(const [u,topics] of Object.entries(units)){cards+=`<div class="item"><div class="cell-title">${u}</div><div style="margin-top:8px">${topics.map(t=>`<span class="badge neutral">${t}</span>`).join(" ")}</div></div>`}cards+="</div>"}
 shell(`${pageHead("Ders ve Üniteler","Ders, ünite ve alt konu yapısını yönetin.",`<button class="btn primary" onclick="currModal()">+ Müfredat Ekle</button>`)}<div class="list">${cards||emptyState("Müfredat boş","Ders ve konu ekleyerek başlayın.")}</div>`,"curriculum")
}
