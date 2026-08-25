const http=require("http"),fs=require("fs"),path=require("path");
const port=Number(process.env.PORT||43127), pub=path.join(__dirname,"public");
http.createServer((req,res)=>{
  const u=new URL(req.url,"http://127.0.0.1");
  if(u.pathname==="/health"){
    res.writeHead(200,{"Content-Type":"application/json; charset=utf-8"});
    return res.end(JSON.stringify({ok:true,version:"0.4.0"}));
  }
  let p=u.pathname==="/"?"/index.html":u.pathname;
  const f=path.normalize(path.join(pub,p));
  if(!f.startsWith(pub)){res.writeHead(403);return res.end("Forbidden")}
  fs.readFile(f,(e,d)=>{
    if(e){res.writeHead(404);return res.end("Not found")}
    const ext=path.extname(f).toLowerCase();
    const types={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".json":"application/json; charset=utf-8"};
    res.writeHead(200,{"Content-Type":types[ext]||"application/octet-stream"});res.end(d);
  });
}).listen(port,"127.0.0.1",()=>console.log("READY 0.4.0"));
