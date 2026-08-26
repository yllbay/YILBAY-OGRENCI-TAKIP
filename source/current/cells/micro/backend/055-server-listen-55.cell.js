http.createServer(async(req,res)=>{
  try{
    const u=new URL(req.url,"http://127.0.0.1");
    if(u.pathname==="/health") return json(res,200,{ok:true,version:"0.10.1",integrations:integrationStatus()});
    if(u.pathname==="/api/integrations/status"&&req.method==="GET") return json(res,200,{ok:true,...integrationStatus()});
    if(u.pathname==="/api/ai/costs"&&req.method==="GET") return json(res,200,{ok:true,...costSummary()});
    if(u.pathname==="/api/drive/status"&&req.method==="GET"){const d=integrationStatus().drive;return json(res,200,{ok:true,...d})}
    if(u.pathname==="/api/drive/oauth/start"&&req.method==="POST") return await handleDriveOauthStart(req,res);
    if(u.pathname==="/api/drive/oauth/callback"&&req.method==="GET") return await handleDriveOauthCallback(u,res);
    if(u.pathname==="/api/drive/index"&&req.method==="POST") return await handleDriveIndex(req,res);
    if(u.pathname==="/api/drive/disconnect"&&req.method==="POST"){const old=readStoredSecrets();writeSecrets({...old,driveRefreshToken:"",driveAccessToken:"",driveAccessTokenExpiresAt:0,driveOauthState:""});return json(res,200,{ok:true})}
    if(u.pathname==="/api/integrations/settings"&&req.method==="POST"){
      const b=await readJson(req,128*1024),old=readStoredSecrets();
      writeSecrets({
        ...old,
        openaiApiKey:b.openaiApiKey==="__KEEP__"?old.openaiApiKey:b.openaiApiKey,
        youtubeApiKey:b.youtubeApiKey==="__KEEP__"?old.youtubeApiKey:b.youtubeApiKey,
        driveClientId:b.driveClientId==="__KEEP__"?old.driveClientId:b.driveClientId,
        driveClientSecret:b.driveClientSecret==="__KEEP__"?old.driveClientSecret:b.driveClientSecret,
        driveFolderId:b.driveFolderId==="__KEEP__"?old.driveFolderId:b.driveFolderId,
        openaiModel:b.openaiModel||old.openaiModel||"gpt-5.6-luna",
        usdTry:b.usdTry??old.usdTry??48.12,
        monthlyBudgetTry:b.monthlyBudgetTry??old.monthlyBudgetTry??1000
      });
      return json(res,200,{ok:true,...integrationStatus()});
    }
    if(u.pathname==="/api/ai/ping"&&req.method==="POST") return await handleAiPing(req,res);
    if(u.pathname==="/api/ai/plan"&&req.method==="POST") return await handleAiPlan(req,res);
    if(u.pathname==="/api/ai/analyze-homework"&&req.method==="POST") return await handleHomework(req,res);
    if(u.pathname==="/api/youtube/search"&&req.method==="POST") return await handleYoutube(req,res);
    let p=u.pathname==="/"?"/index.html":u.pathname;
    const f=path.normalize(path.join(pub,p));
    if(!f.startsWith(pub)){res.writeHead(403);return res.end("Forbidden")}
    fs.readFile(f,(e,d)=>{
      if(e){res.writeHead(404);return res.end("Not found")}
      const ext=path.extname(f).toLowerCase();
      const types={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".json":"application/json; charset=utf-8"};
      res.writeHead(200,{"Content-Type":types[ext]||"application/octet-stream"});res.end(d);
    });
  }catch(e){
    console.error("REQUEST_ERROR",e);
    if(!res.headersSent) json(res,500,{ok:false,error:e.message||"Sunucu hatası"});
  }
}).listen(port,"127.0.0.1",()=>console.log("READY 0.6.8"));
