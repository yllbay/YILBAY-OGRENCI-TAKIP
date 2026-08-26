function exams(){
 const rows=db.exams.map(e=>`<tr><td><div class="cell-title">${e.title}</div></td><td>${e.course}</td><td>${e.topic}</td><td>${e.url?`<a href="${e.url}" target="_blank">Sınavı aç</a>`:"—"}</td></tr>`).join("");
 shell(`${pageHead("Online Sınavlar","Online test ve sınav bağlantılarını konu bazında yönetin.",`<button class="btn primary" onclick="examModal()">+ Sınav Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Sınav</th><th>Ders</th><th>Konu</th><th>Bağlantı</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Online sınav yok","İlk sınav bağlantısını ekleyin.")}`,"exams")
}
