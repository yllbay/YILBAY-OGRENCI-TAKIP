/* CELL:30-curriculum | layer:frontend | generated-from:v0.7.2 */
function curriculum(){
 let cards="";for(const [course,units] of Object.entries(db.curriculum)){cards+=`<div class="card"><div class="section-head"><h2 style="margin:0">${course}</h2><span class="badge info">${Object.values(units).reduce((n,x)=>n+x.length,0)} konu</span></div>`;for(const [u,topics] of Object.entries(units)){cards+=`<div class="item"><div class="cell-title">${u}</div><div style="margin-top:8px">${topics.map(t=>`<span class="badge neutral">${t}</span>`).join(" ")}</div></div>`}cards+="</div>"}
 shell(`${pageHead("Ders ve Üniteler","Ders, ünite ve alt konu yapısını yönetin.",`<button class="btn primary" onclick="currModal()">+ Müfredat Ekle</button>`)}<div class="list">${cards||emptyState("Müfredat boş","Ders ve konu ekleyerek başlayın.")}</div>`,"curriculum")
}
window.currModal=()=>modal(`<h2>Müfredat Ekle</h2><div class="formgrid"><div class="field"><label>Ders</label><input id="ccourse"></div><div class="field"><label>Ünite</label><input id="cunit"></div><div class="field"><label>Alt ünite / konu</label><input id="ctopic"></div></div><div class="modal-actions"><button class="btn primary" onclick="addCurr()">Kaydet</button></div>`)
window.addCurr=()=>{let c=q("ccourse").value.trim(),u=q("cunit").value.trim(),t=q("ctopic").value.trim();if(!c||!u||!t)return alert("Tüm alanlar gerekli");db.curriculum[c]??={};db.curriculum[c][u]??=[];if(!db.curriculum[c][u].includes(t))db.curriculum[c][u].push(t);save();closeModal();curriculum()}
function topicOptions(){let out="";for(const [c,units] of Object.entries(db.curriculum))for(const topics of Object.values(units))for(const t of topics)out+=`<option data-course="${c}" value="${c}|||${t}">${c} — ${t}</option>`;return out}

/* CELL:40-resources | layer:frontend | generated-from:v0.8.0 */
