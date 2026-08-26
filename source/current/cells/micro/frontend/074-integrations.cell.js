function integrations(){
 shell(`${pageHead("AI ve API Entegrasyonları","OpenAI ile adaptif planlama/ödev analizi, YouTube ile konu anlatım videosu seçimi. API anahtarları tarayıcıya kaydedilmez.",`<button class="btn primary" onclick="testOpenAIConnection()">OpenAI Bağlantısını Test Et</button>`)}
 <div id="integrationStatus"><div class="card">Entegrasyon durumu okunuyor…</div></div>
 <div class="section"><div class="section-head"><h2>Güvenlik</h2></div><div class="notice"><div><b>Sunucu tarafı anahtar saklama</b>Anahtarlar LocalStorage veya uygulama JavaScript dosyasına yazılmaz. Kalıcı paketin <code>runtime</code> alanında tutulur ve mevcut teşhis raporuna eklenmez.</div></div></div>`,"integrations");
 loadIntegrationStatus()
}


