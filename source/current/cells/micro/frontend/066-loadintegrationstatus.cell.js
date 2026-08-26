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


