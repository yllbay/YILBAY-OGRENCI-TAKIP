function readSecrets(){
  const stored=readStoredSecrets();
  const envKey=String(process.env.OPENAI_API_KEY||"").trim();
  const manual=String(stored.openaiApiKey||"").trim();
  let openaiApiKey="",openaiApiSource="none";
  if(envKey){ openaiApiKey=envKey; openaiApiSource="environment"; }
  else if(manual){ openaiApiKey=manual; openaiApiSource="manual"; }
  return {...stored,openaiApiKey,openaiApiSource,credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:{method:"disabled-environment-mode",found:false,userMatch:false,targetMatched:false}};
}


