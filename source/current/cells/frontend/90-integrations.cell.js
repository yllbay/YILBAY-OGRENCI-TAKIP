/* CELL:90-integrations | layer:frontend | generated-from:v0.7.2 */
function integrations(){
 shell(`${pageHead("AI ve API Entegrasyonları","OpenAI ile adaptif planlama/ödev analizi, YouTube ile konu anlatım videosu seçimi. API anahtarları tarayıcıya kaydedilmez.",`<button class="btn primary" onclick="testOpenAIConnection()">OpenAI Bağlantısını Test Et</button>`)}
 <div id="integrationStatus"><div class="card">Entegrasyon durumu okunuyor…</div></div>
 <div class="section"><div class="section-head"><h2>Güvenlik</h2></div><div class="notice"><div><b>Sunucu tarafı anahtar saklama</b>Anahtarlar LocalStorage veya uygulama JavaScript dosyasına yazılmaz. Kalıcı paketin <code>runtime</code> alanında tutulur ve mevcut teşhis raporuna eklenmez.</div></div></div>`,"integrations");
 loadIntegrationStatus()
}
async function loadIntegrationStatus(){
 try{
  const s=await apiJson("/api/integrations/status");
  const c=await apiJson("/api/ai/costs");
  q("integrationStatus").innerHTML=`<div class="integration-grid">
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">OpenAI</div><div class="cell-sub">Planlama + ödev vision analizi</div></div><span class="badge ${s.openai.configured?"good":"mid"}">${s.openai.configured?"Bağlı":"Anahtar gerekli"}</span></div><div class="integration-meta">Model: <b>${s.openai.model}</b><br>Kaynak: <b>${s.openai.source==="windows-credential-manager"?"Windows Kimlik Bilgileri Yöneticisi":s.openai.source==="environment"?"Ortam değişkeni":s.openai.source==="manual"?"Manuel ayar":"Yok"}</b>${s.openai.source==="windows-credential-manager"?` · ${s.openai.credentialTarget}`:""}</div></div>
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">YouTube Data API</div><div class="cell-sub">Konu anlatım videosu arama</div></div><span class="badge ${s.youtube.configured?"good":"mid"}">${s.youtube.configured?"Bağlı":"Anahtar gerekli"}</span></div><div class="integration-meta">Türkçe video araması ve güvenli arama</div></div>
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">Google Drive</div><div class="cell-sub">PDF kaynak havuzu</div></div><span class="badge info">Aşama 2</span></div><div class="integration-meta">Şimdilik kaynak kayıtlarındaki Drive bağlantıları kullanılır; OAuth bağlantısı sonraki adım.</div></div>
   <div class="card integration-card"><div class="integration-head"><div><div class="cell-title">Bu ay AI maliyeti</div><div class="cell-sub">${c.operations} ücretli AI işlemi</div></div><span class="badge ${c.budgetPercent<70?"good":c.budgetPercent<90?"mid":"low"}">${c.totalTry.toFixed(2)} TL</span></div><div class="integration-meta">Bütçe: ${c.budgetTry.toFixed(0)} TL · Kalan: ${c.remainingTry.toFixed(2)} TL · İşlem ort.: ${c.averageTry.toFixed(3)} TL</div></div>
  </div>
  <div class="grid">
   <div class="card kpi-card"><div class="kpi-label">Planlama</div><div class="kpi">${Number(c.byOperation.plan||0).toFixed(2)} TL</div><div class="kpi-foot">AI dönem planı</div></div>
   <div class="card kpi-card"><div class="kpi-label">Ödev analizi</div><div class="kpi">${Number(c.byOperation.homework_analysis||0).toFixed(2)} TL</div><div class="kpi-foot">PDF / vision değerlendirme</div></div>
   <div class="card kpi-card"><div class="kpi-label">Kur</div><div class="kpi">${c.usdTry.toFixed(2)}</div><div class="kpi-foot">1 USD → TL maliyet hesabı</div></div>
  </div>
  <div class="section"><button class="btn primary" onclick="integrationSettingsModal()">API Ayarlarını Aç</button></div>`
 }catch(e){q("integrationStatus").innerHTML=`<div class="notice error">${e.message}</div>`}
}
window.integrationSettingsModal=()=>modal(`<h2>API Ayarları</h2><p class="muted">Mevcut anahtarı korumak için alanı boş bırakabilirsiniz.</p><div class="formgrid">
 <div class="field"><label>OpenAI API Key</label><input id="openaiKey" type="password" autocomplete="off" placeholder="sk-..."></div>
 <div class="field"><label>OpenAI Modeli</label><select id="openaiModel"><option value="gpt-5.6-luna">GPT-5.6 Luna — düşük maliyet</option><option value="gpt-5.6-terra">GPT-5.6 Terra — daha yüksek kalite</option><option value="gpt-5.6-sol">GPT-5.6 Sol — en yüksek kalite</option></select></div>
 <div class="field" style="grid-column:1/-1"><label>YouTube Data API Key</label><input id="youtubeKey" type="password" autocomplete="off" placeholder="AIza..."></div>
 <div class="field"><label>USD/TL Maliyet Kuru</label><input id="usdTry" type="number" step="0.01" min="1" value="48.12"></div>
 <div class="field"><label>Aylık AI Bütçe Limiti (TL)</label><input id="monthlyBudgetTry" type="number" step="10" min="10" value="1000"></div>
 </div><div class="modal-actions"><button class="btn primary" onclick="saveIntegrationSettings()">Kaydet</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
window.saveIntegrationSettings=async()=>{
 try{
  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;
  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;
  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});
  closeModal();integrations()
 }catch(e){alert("Ayar kaydedilemedi: "+e.message)}
}
window.testOpenAIConnection=async()=>{
 const btn=[...document.querySelectorAll("button")].find(x=>x.textContent.includes("OpenAI Bağlantısını Test Et"));
 const old=btn?.textContent;if(btn){btn.disabled=true;btn.textContent="Test ediliyor…"}
 try{
  const r=await apiJson("/api/ai/ping",{});
  alert(`OpenAI bağlantısı başarılı.\nModel: ${r.model}\nGecikme: ${r.latencyMs} ms${r.cost?`\nMaliyet: ${Number(r.cost.try||0).toFixed(4)} TL`:""}`);
  loadIntegrationStatus();
 }catch(e){alert("OpenAI bağlantı testi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent=old||"OpenAI Bağlantısını Test Et"}}
}
