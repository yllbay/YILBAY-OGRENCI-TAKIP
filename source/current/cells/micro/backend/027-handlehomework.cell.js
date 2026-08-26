

async function handleHomework(req,res){
  const body=await readJson(req,18*1024*1024);
  const {fileData,mimeType="application/pdf",fileName="odev.pdf",assignment,answerKey=null}=body;
  if(!fileData) return json(res,400,{ok:false,error:"Ödev dosyası gerekli"});
  if(!integrationStatus().openai.configured) return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun. Yüklenen PDF/görselde öğrencinin işaretlerini, boş bıraktığı soruları ve mümkünse çözüm yollarını incele.
Eğer cevap anahtarı sağlandıysa onu kesin referans olarak kullan. Cevap anahtarı yoksa yalnızca güvenle değerlendirebildiklerini puanla ve confidence değerini düşür.
Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.
Kesin göremediğin işaret veya çözüm için tahmin yürütme. Soruların/işaretlerin yeterli kısmı okunamıyorsa needsTeacherReview=true yap.
confidence 0 ile 1 arasında olmalı. confidence 0.65 altındaysa sonuç öğretmen onayı gerektirmelidir.
Sadece JSON döndür:
{"totalQuestions":number,"correct":number,"wrong":number,"blank":number,"scorePercent":number,"confidence":number,"items":[{"question":number,"status":"correct|wrong|blank|uncertain","studentAnswer":"string|null","correctAnswer":"string|null","errorType":"string|null","note":"string|null"}],"weaknesses":["..."],"recommendRepeat":boolean,"summary":"..."}`;
  const content=[
    {type:"input_text",text:JSON.stringify({assignment,answerKey})},
    {type:"input_file",filename:fileName,file_data:`data:${mimeType};base64,${fileData}`}
  ];
  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"medium"});
  const parsed=normalizeHomeworkAnalysis(parseJsonText(ai.text));
  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});
}

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */
async function handleYoutube(req,res){
  const body=await readJson(req,512*1024);
  const s=readSecrets();
  if(!s.youtubeApiKey) return json(res,400,{ok:false,error:"YouTube API anahtarı ayarlanmamış"});
  const query=String(body.query||"").trim();
  if(!query) return json(res,400,{ok:false,error:"Arama metni gerekli"});
  const max=Math.min(10,Math.max(1,Number(body.maxResults||5)));
  const u=new URL("https://www.googleapis.com/youtube/v3/search");
  u.searchParams.set("part","snippet");u.searchParams.set("type","video");u.searchParams.set("maxResults",String(max));
  u.searchParams.set("q",query);u.searchParams.set("key",s.youtubeApiKey);
  u.searchParams.set("safeSearch","strict");u.searchParams.set("relevanceLanguage","tr");
  const r=await fetch(u);const data=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data?.error?.message||`YouTube API HTTP ${r.status}`);
  const videos=(data.items||[]).map(v=>({
    videoId:v.id?.videoId,title:v.snippet?.title,channelTitle:v.snippet?.channelTitle,
    publishedAt:v.snippet?.publishedAt,thumbnail:v.snippet?.thumbnails?.medium?.url||v.snippet?.thumbnails?.default?.url,
    url:v.id?.videoId?`https://www.youtube.com/watch?v=${v.id.videoId}`:""
  }));
  json(res,200,{ok:true,videos});
}

/* CELL:70-routes | layer:backend | generated-from:v0.7.2 */

/* CELL:70-routes | layer:backend | generated-from:v0.7.2 */
http.createServer(async(req,res)=>{
  try{
    const u=new URL(req.url,"http://127.0.0.1");
    if(u.pathname==="/health") return json(res,200,{ok:true,version:"0.8.1",integrations:integrationStatus()});
    if(u.pathname==="/api/integrations/status"&&req.method==="GET") return json(res,200,{ok:true,...integrationStatus()});
    if(u.pathname==="/api/ai/costs"&&req.method==="GET") return json(res,200,{ok:true,...costSummary()});
    if(u.pathname==="/api/integrations/settings"&&req.method==="POST"){
      const b=await readJson(req,128*1024),old=readStoredSecrets();
      writeSecrets({
        openaiApiKey:b.openaiApiKey==="__KEEP__"?old.openaiApiKey:b.openaiApiKey,
        youtubeApiKey:b.youtubeApiKey==="__KEEP__"?old.youtubeApiKey:b.youtubeApiKey,
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
