

function integrationStatus(){
  const s=readSecrets();
  return {
    openai:{configured:!!s.openaiApiKey,model:s.openaiModel||"gpt-5.6-luna",source:s.openaiApiSource||"none",credentialTarget:OPENAI_CREDENTIAL_TARGET,credentialDiagnostic:s.credentialDiagnostic||null},
    youtube:{configured:!!s.youtubeApiKey},
    drive:{configured:false,mode:"resource-metadata"},
    cost:{usdTry:Number(s.usdTry||48.12)||48.12,monthlyBudgetTry:Number(s.monthlyBudgetTry||1000)||1000}
  };
}

/* CELL:20-cost-accounting | layer:backend | generated-from:v0.7.2 */

/* CELL:20-cost-accounting | layer:backend | generated-from:v0.7.2 */
const OPENAI_PRICES={
  "gpt-5.6-luna":{input:0.20,cached:0.02,output:1.20},
  "gpt-5.6-terra":{input:2.00,cached:0.20,output:12.00},
  "gpt-5.6-sol":{input:4.00,cached:0.40,output:20.00}
};
