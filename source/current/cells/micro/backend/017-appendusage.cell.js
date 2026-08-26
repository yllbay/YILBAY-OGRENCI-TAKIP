

function appendUsage(operation,model,usage,meta={}){
  try{
    const cost=estimateCost(model,usage);
    const row={ts:new Date().toISOString(),operation,model,...cost,meta};
    fs.appendFileSync(usageFile,JSON.stringify(row)+"\n","utf8");
    return row;
  }catch{return null}
}
