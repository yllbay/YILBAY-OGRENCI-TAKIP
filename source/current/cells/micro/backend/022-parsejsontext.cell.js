

function parseJsonText(txt){
  const raw=String(txt||"").trim().replace(/^```(?:json)?\s*/i,"").replace(/\s*```$/,"");
  try{return JSON.parse(raw)}catch{}
  const a=raw.indexOf("{"),b=raw.lastIndexOf("}");
  if(a>=0&&b>a) return JSON.parse(raw.slice(a,b+1));
  throw new Error("AI yanıtı JSON olarak ayrıştırılamadı");
}
