

async function openaiRequest({instructions,input,reasoning="low"}){
  const s=readSecrets();
  if(!s.openaiApiKey) throw new Error("OpenAI API anahtarı ayarlanmamış");
  const body={
    model:s.openaiModel||"gpt-5.6-luna",
    reasoning:{effort:reasoning},
    instructions,
    input,
    text:{verbosity:"low"}
  };
  const r=await fetch("https://api.openai.com/v1/responses",{
    method:"POST",
    headers:{"Authorization":`Bearer ${s.openaiApiKey}`,"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data?.error?.message||`OpenAI API HTTP ${r.status}`);
  return {data,text:extractOutputText(data),model:body.model};
}
