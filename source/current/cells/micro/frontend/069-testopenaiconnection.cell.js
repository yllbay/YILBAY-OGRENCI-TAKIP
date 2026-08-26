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

/* CELL:100-ai-planner | layer:frontend | generated-from:v0.8.2 */

/* CELL:100-ai-planner | layer:frontend | generated-from:v0.7.2 */
