

function extractOutputText(data){
  if(typeof data?.output_text==="string") return data.output_text;
  const out=[];
  for(const item of data?.output||[]){
    for(const c of item?.content||[]){
      if(typeof c?.text==="string") out.push(c.text);
    }
  }
  return out.join("\n");
}
