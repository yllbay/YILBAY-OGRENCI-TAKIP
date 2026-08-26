/* CELL:20-cost-accounting | layer:backend | generated-from:v0.7.2 */
const OPENAI_PRICES={
  "gpt-5.6-luna":{input:0.20,cached:0.02,output:1.20},
  "gpt-5.6-terra":{input:2.00,cached:0.20,output:12.00},
  "gpt-5.6-sol":{input:4.00,cached:0.40,output:20.00}
};
function usageNumbers(usage={}){
  const input=Number(usage.input_tokens||0);
  const output=Number(usage.output_tokens||0);
  const cached=Number(usage.input_tokens_details?.cached_tokens||0);
  return {input,output,cached,uncached:Math.max(0,input-cached)};
}
function estimateCost(model,usage={}){
  const p=OPENAI_PRICES[model]||OPENAI_PRICES["gpt-5.6-luna"];
  const u=usageNumbers(usage);
  const usd=(u.uncached*p.input+u.cached*p.cached+u.output*p.output)/1_000_000;
  const fx=integrationStatus().cost.usdTry;
  return {...u,usd,try:usd*fx};
}
function appendUsage(operation,model,usage,meta={}){
  try{
    const cost=estimateCost(model,usage);
    const row={ts:new Date().toISOString(),operation,model,...cost,meta};
    fs.appendFileSync(usageFile,JSON.stringify(row)+"\n","utf8");
    return row;
  }catch{return null}
}
function readUsageRows(){
  try{
    return fs.readFileSync(usageFile,"utf8").split(/\r?\n/).filter(Boolean).map(x=>JSON.parse(x));
  }catch{return []}
}
function costSummary(){
  const rows=readUsageRows(), now=new Date(), ym=now.toISOString().slice(0,7);
  const month=rows.filter(r=>String(r.ts||"").slice(0,7)===ym);
  const sum=a=>a.reduce((n,r)=>n+Number(r.try||0),0);
  const byOperation={};
  for(const r of month) byOperation[r.operation]=(byOperation[r.operation]||0)+Number(r.try||0);
  const totalTry=sum(month), cfg=integrationStatus().cost;
  return {
    month:ym,
    totalTry,
    totalUsd:month.reduce((n,r)=>n+Number(r.usd||0),0),
    operations:month.length,
    averageTry:month.length?totalTry/month.length:0,
    byOperation,
    budgetTry:cfg.monthlyBudgetTry,
    remainingTry:Math.max(0,cfg.monthlyBudgetTry-totalTry),
    budgetPercent:cfg.monthlyBudgetTry?Math.min(999,100*totalTry/cfg.monthlyBudgetTry):0,
    usdTry:cfg.usdTry,
    recent:rows.slice(-20).reverse()
  };
}

/* CELL:30-http-openai-core | layer:backend | generated-from:v0.7.2 */
