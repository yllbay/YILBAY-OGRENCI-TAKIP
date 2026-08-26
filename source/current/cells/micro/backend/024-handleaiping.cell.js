

async function handleAiPing(req,res){
  const status=integrationStatus();
  if(!status.openai.configured) return json(res,400,{ok:false,error:"OpenAI API anahtarı bağlı değil"});
  const started=Date.now();
  const ai=await openaiRequest({instructions:"Yalnızca OK yaz.",input:"Bağlantı testi",reasoning:"low"});
  const cost=appendUsage("connection_test",ai.model,ai.data?.usage||{},{});
  return json(res,200,{ok:true,connected:true,model:ai.model,latencyMs:Date.now()-started,response:String(ai.text||"").trim().slice(0,80),usage:ai.data?.usage||null,cost});
}

/* CELL:40-academic-planner | layer:backend | generated-from:v0.7.2 */

/* CELL:40-academic-planner | layer:backend | generated-from:v0.7.2 */
function flattenCurriculum(curriculum,courses){
  const rows=[];
  for(const course of courses||[]){
    const units=curriculum?.[course]||{};
    for(const [unit,topics] of Object.entries(units)){
      for(const topic of topics||[]) rows.push({course,unit,topic});
    }
  }
  return rows;
}
