function writeSecrets(next){
  const clean={
    openaiApiKey:String(next.openaiApiKey||"").trim(),
    youtubeApiKey:String(next.youtubeApiKey||"").trim(),
    driveClientId:String(next.driveClientId||"").trim(),
    driveClientSecret:String(next.driveClientSecret||"").trim(),
    driveFolderId:String(next.driveFolderId||"").trim(),
    driveRefreshToken:String(next.driveRefreshToken||"").trim(),
    driveAccessToken:String(next.driveAccessToken||"").trim(),
    driveAccessTokenExpiresAt:Number(next.driveAccessTokenExpiresAt||0)||0,
    driveOauthState:String(next.driveOauthState||"").trim(),
    openaiModel:String(next.openaiModel||"gpt-5.6-luna").trim()||"gpt-5.6-luna",
    usdTry:Number(next.usdTry||48.12)||48.12,
    monthlyBudgetTry:Number(next.monthlyBudgetTry||1000)||1000
  };
  fs.writeFileSync(secretFile,JSON.stringify(clean,null,2),"utf8");
  return clean;
}


