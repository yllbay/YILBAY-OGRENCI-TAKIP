function writeSecrets(next){
  const clean={
    openaiApiKey:String(next.openaiApiKey||"").trim(),
    youtubeApiKey:String(next.youtubeApiKey||"").trim(),
    openaiModel:String(next.openaiModel||"gpt-5.6-luna").trim()||"gpt-5.6-luna",
    usdTry:Number(next.usdTry||48.12)||48.12,
    monthlyBudgetTry:Number(next.monthlyBudgetTry||1000)||1000
  };
  fs.writeFileSync(secretFile,JSON.stringify(clean,null,2),"utf8");
  return clean;
}


