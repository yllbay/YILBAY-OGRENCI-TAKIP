

async function readJson(req,max=18*1024*1024){
  return await new Promise((resolve,reject)=>{
    let size=0,chunks=[];
    req.on("data",c=>{size+=c.length;if(size>max){reject(new Error("İstek çok büyük"));req.destroy();return}chunks.push(c)});
    req.on("end",()=>{try{resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")||"{}"))}catch(e){reject(new Error("Geçersiz JSON"))}});
    req.on("error",reject);
  });
}
