window.saveIntegrationSettings=async()=>{
 try{
  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;
  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;
  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});
  closeModal();integrations()
 }catch(e){alert("Ayar kaydedilemedi: "+e.message)}
}
