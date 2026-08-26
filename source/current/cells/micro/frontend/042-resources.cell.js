function resources(){
 const rows=db.resources.map(r=>`<tr><td><div class="cell-title">${r.title}</div><div class="cell-sub">${r.type||"PDF"}</div></td><td>${r.course}</td><td>${r.topic}</td><td><span class="badge neutral">${r.level}</span></td></tr>`).join("");
 shell(`${pageHead("Kaynak Havuzu","PDF ödev ve çalışma kaynaklarını ders, konu ve zorluk düzeyine göre yönetin.",`<button class="btn primary" onclick="resourceModal()">+ Kaynak Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Kaynak</th><th>Ders</th><th>Konu</th><th>Seviye</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Kaynak bulunamadı","İlk PDF kaynağınızı ekleyin.")}`,"resources")
}
