function estimateCost(model,usage={}){
  const p=OPENAI_PRICES[model]||OPENAI_PRICES["gpt-5.6-luna"];
  const u=usageNumbers(usage);
  const usd=(u.uncached*p.input+u.cached*p.cached+u.output*p.output)/1_000_000;
  const fx=integrationStatus().cost.usdTry;
  return {...u,usd,try:usd*fx};
}


