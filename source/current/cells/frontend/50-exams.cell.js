/* CELL:50-exams | layer:frontend | generated-from:v0.7.2 */
function exams(){
 const rows=db.exams.map(e=>`<tr><td><div class="cell-title">${e.title}</div></td><td>${e.course}</td><td>${e.topic}</td><td>${e.url?`<a href="${e.url}" target="_blank">Sınavı aç</a>`:"—"}</td></tr>`).join("");
 shell(`${pageHead("Online Sınavlar","Online test ve sınav bağlantılarını konu bazında yönetin.",`<button class="btn primary" onclick="examModal()">+ Sınav Ekle</button>`)}${rows?tableWrap(`<table><thead><tr><th>Sınav</th><th>Ders</th><th>Konu</th><th>Bağlantı</th></tr></thead><tbody>${rows}</tbody></table>`):emptyState("Online sınav yok","İlk sınav bağlantısını ekleyin.")}`,"exams")
}
window.examModal=()=>modal(`<h2>Online Sınav Ekle</h2><div class="formgrid"><div class="field"><label>Başlık</label><input id="etitle"></div><div class="field"><label>Konu</label><select id="etopic">${topicOptions()}</select></div><div class="field"><label>Link</label><input id="eurl"></div></div><div class="modal-actions"><button class="btn primary" onclick="addExam()">Kaydet</button></div>`)
window.addExam=()=>{const [course,topic]=q("etopic").value.split("|||");db.exams.push({id:Date.now(),course,topic,title:q("etitle").value||topic+" Online Test",url:q("eurl").value});save();closeModal();exams()}

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.8.0 */
