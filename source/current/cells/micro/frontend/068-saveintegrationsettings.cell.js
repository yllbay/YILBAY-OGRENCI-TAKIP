window.saveIntegrationSettings=async()=>{
 try{
  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;
  const driveClientId=q("driveClientId").value.trim(),driveClientSecret=q("driveClientSecret").value.trim(),driveFolderId=q("driveFolderId").value.trim();
  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;
  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",driveClientId:driveClientId||"__KEEP__",driveClientSecret:driveClientSecret||"__KEEP__",driveFolderId:driveFolderId||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});
  closeModal();integrations()
 }catch(e){alert("Ayar kaydedilemedi: "+e.message)}
}
