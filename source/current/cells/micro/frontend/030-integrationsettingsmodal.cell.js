

window.integrationSettingsModal=()=>modal(`<h2>API Ayarları</h2><p class="muted">Mevcut anahtarı korumak için alanı boş bırakabilirsiniz.</p><div class="formgrid">
 <div class="field"><label>OpenAI API Key</label><input id="openaiKey" type="password" autocomplete="off" placeholder="sk-..."></div>
 <div class="field"><label>OpenAI Modeli</label><select id="openaiModel"><option value="gpt-5.6-luna">GPT-5.6 Luna — düşük maliyet</option><option value="gpt-5.6-terra">GPT-5.6 Terra — daha yüksek kalite</option><option value="gpt-5.6-sol">GPT-5.6 Sol — en yüksek kalite</option></select></div>
 <div class="field" style="grid-column:1/-1"><label>YouTube Data API Key</label><input id="youtubeKey" type="password" autocomplete="off" placeholder="AIza..."></div>
 <div class="field"><label>USD/TL Maliyet Kuru</label><input id="usdTry" type="number" step="0.01" min="1" value="48.12"></div>
 <div class="field"><label>Aylık AI Bütçe Limiti (TL)</label><input id="monthlyBudgetTry" type="number" step="10" min="10" value="1000"></div>
 </div><div class="modal-actions"><button class="btn primary" onclick="saveIntegrationSettings()">Kaydet</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
window.saveIntegrationSettings=async()=>{
 try{
  const openaiApiKey=q("openaiKey").value.trim(),youtubeApiKey=q("youtubeKey").value.trim(),openaiModel=q("openaiModel").value;
  const usdTry=Number(q("usdTry").value)||48.12,monthlyBudgetTry=Number(q("monthlyBudgetTry").value)||1000;
  await apiJson("/api/integrations/settings",{openaiApiKey:openaiApiKey||"__KEEP__",youtubeApiKey:youtubeApiKey||"__KEEP__",openaiModel,usdTry,monthlyBudgetTry});
  closeModal();integrations()
 }catch(e){alert("Ayar kaydedilemedi: "+e.message)}
}
window.testOpenAIConnection=async()=>{
 const btn=[...document.querySelectorAll("button")].find(x=>x.textContent.includes("OpenAI Bağlantısını Test Et"));
 const old=btn?.textContent;if(btn){btn.disabled=true;btn.textContent="Test ediliyor…"}
 try{
  const r=await apiJson("/api/ai/ping",{});
  alert(`OpenAI bağlantısı başarılı.\nModel: ${r.model}\nGecikme: ${r.latencyMs} ms${r.cost?`\nMaliyet: ${Number(r.cost.try||0).toFixed(4)} TL`:""}`);
  loadIntegrationStatus();
 }catch(e){alert("OpenAI bağlantı testi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent=old||"OpenAI Bağlantısını Test Et"}}
}

/* CELL:100-ai-planner | layer:frontend | generated-from:v0.8.1 */

/* CELL:100-ai-planner | layer:frontend | generated-from:v0.7.2 */
window.generateAiMasterPlan=async()=>{
 const s=db.students.find(x=>x.id===selectedStudentId);if(!s)return;
 const key=String(s.id);
 const oldText=document.querySelector(".page-actions .btn.primary")?.textContent;
 const btn=document.querySelector(".page-actions .btn.primary");if(btn){btn.disabled=true;btn.textContent="AI planlıyor…"}
 try{
  const data=await apiJson("/api/ai/plan",{student:s,curriculum:db.curriculum,results:db.results.filter(r=>r.studentId===s.id),resources:db.resources});
  db.aiPlans[key]=data;
  const weeks=data.plan?.weeks||[];
  const now=new Date(),start=new Date(s.registeredAt||now),idx=Math.max(0,Math.min(weeks.length-1,Math.floor((now-start)/(7*864e5))));
  const source=weeks[idx]?.items||weeks[0]?.items||[];
  const allowed=DAY_NAMES.slice(0,Math.max(1,Math.min(7,s.weeklyStudyDays||6))),days=Object.fromEntries(DAY_NAMES.map(d=>[d,[]]));
  source.forEach((x,i)=>{
    const res=db.resources.find(r=>r.id===x.resourceId);
    days[allowed[i%allowed.length]].push({type:x.type||"Yeni Konu",course:x.course,topic:x.topic,level:s.levels?.[x.course]||"Orta",resource:res?.title||"Kaynak seçilecek",exam:"—",reason:x.reason||"AI dönem planı",priority:x.priority==="high"?0:1})
  });
  db.weeklyPlans[key]={generatedAt:new Date().toISOString(),days,source:"ai"};
  save();program();
  alert(data.usedAi?`AI dönem planı oluşturuldu.${data.cost?`\nBu işlem: ${Number(data.cost.try||0).toFixed(3)} TL`:""}`:"API anahtarı olmadığı için kural tabanlı dönem planı oluşturuldu.")
 }catch(e){alert("AI planlama hatası: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent=oldText||"AI ile Dönem Planı Üret"}}
}

/* CELL:110-youtube | layer:frontend | generated-from:v0.8.1 */

/* CELL:110-youtube | layer:frontend | generated-from:v0.7.2 */
window.findTopicVideo=async(course,topic)=>{
 try{
  const key=course+"|||"+topic;
  modal(`<h2>Konu Anlatım Videosu</h2><div id="videoResults"><div class="muted">YouTube aranıyor…</div></div><div class="modal-actions"><button class="btn ghost" onclick="closeModal()">Kapat</button></div>`);
  const data=await apiJson("/api/youtube/search",{query:`${course} ${topic} konu anlatımı YKS TYT AYT`,maxResults:5});
  db.videoSuggestions[key]=data.videos;save();
  q("videoResults").innerHTML=data.videos.length?`<div class="video-list">${data.videos.map((v,i)=>`<a class="video-row" href="${v.url}" target="_blank" rel="noopener"><div class="video-rank">${i+1}</div><div><div class="cell-title">${v.title}</div><div class="cell-sub">${v.channelTitle}</div></div></a>`).join("")}</div>`:emptyState("Video bulunamadı","Arama sorgusunu veya API ayarını kontrol edin.")
 }catch(e){if(q("videoResults"))q("videoResults").innerHTML=`<div class="notice error">${e.message}</div>`;else alert(e.message)}
}

/* CELL:120-ai-homework | layer:frontend | generated-from:v0.8.1 */

/* CELL:120-ai-homework | layer:frontend | generated-from:v0.7.2 */
window.analyzeAssignment=id=>{
 const a=db.assignments.find(x=>x.id===id);if(!a)return;
 modal(`<h2>AI ile Ödev Analizi</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} · ${a.course} / ${a.topic}</p>
 <div class="field"><label>Öğrencinin tamamladığı PDF veya görsel</label><input id="homeworkFile" type="file" accept=".pdf,image/png,image/jpeg,image/webp"></div>
 <div class="field"><label>Cevap anahtarı (opsiyonel)</label><textarea id="answerKey" rows="4" placeholder="Örn: 1-A, 2-C, 3-B..."></textarea></div>
 <div class="notice"><div><b>Analiz kapsamı</b>AI; doğru, yanlış ve boşları; görülebilen çözüm yollarını; hata türlerini ve başarı yüzdesini çıkarır. Cevap anahtarı verilirse doğruluk yükselir.</div></div>
 <div class="modal-actions"><button class="btn primary" onclick="submitHomeworkAnalysis(${id})">Dosyayı Tara</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
}
function fileToBase64(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(",")[1]);r.onerror=reject;r.readAsDataURL(file)})}
window.submitHomeworkAnalysis=async id=>{
 const a=db.assignments.find(x=>x.id===id),file=q("homeworkFile")?.files?.[0];if(!a||!file)return alert("Ödev dosyasını seçin");
 if(file.size>14*1024*1024)return alert("Bu sürümde dosya en fazla 14 MB olabilir.");
 const btn=document.querySelector(".modal-actions .btn.primary");if(btn){btn.disabled=true;btn.textContent="AI tarıyor…"}
 try{
  const fileData=await fileToBase64(file),answerKey=q("answerKey").value.trim()||null;
  const data=await apiJson("/api/ai/analyze-homework",{fileData,mimeType:file.type||"application/pdf",fileName:file.name,assignment:{id:a.id,studentId:a.studentId,course:a.course,topic:a.topic,title:a.title},answerKey});
  const an=data.analysis||{},score=Math.round(Number(an.scorePercent)||0),reviewRequired=!!an.needsTeacherReview||data.autoFinalize===false;
  db.homeworkAnalyses.push({id:Date.now(),assignmentId:a.id,studentId:a.studentId,course:a.course,topic:a.topic,date:new Date().toISOString().slice(0,10),fileName:file.name,fileSize:file.size,mimeType:file.type||"application/pdf",costTry:Number(data.cost?.try||0),...an});
  a.completedAt=new Date().toISOString().slice(0,10);a.score=score;a.aiConfidence=Number(an.confidence||0);
  if(reviewRequired){
    a.status="Öğretmen Kontrolü";
  }else{
    a.status="Tamamlandı";
    db.results.push({id:Date.now()+1,studentId:a.studentId,kind:"AI Ödev Analizi",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});
    if(score<db.threshold&&!db.repeatSignals.some(r=>r.assignmentId===a.id&&r.status==="Bekliyor"))db.repeatSignals.push({id:Date.now()+2,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString()});
  }
  save();
  q("modalbg").querySelector(".modal").innerHTML=`<h2>${reviewRequired?"Öğretmen Kontrolü Gerekli":"Ödev Analizi Tamamlandı"}</h2><div class="result-hero"><div class="kpi">%${score}</div><div><div class="cell-title">${an.correct||0} doğru · ${an.wrong||0} yanlış · ${an.blank||0} boş</div><div class="cell-sub">Güven: %${Math.round((Number(an.confidence)||0)*100)}${data.cost?` · AI maliyeti ${Number(data.cost.try||0).toFixed(4)} TL`:""}</div></div></div>
   ${reviewRequired?`<div class="notice error"><div><b>Otomatik sonuç kesinleştirilmedi</b>AI güveni yeterli olmadığı için bu analiz başarı sonuçlarına ve tekrar motoruna otomatik aktarılmadı. Atamalar ekranından “Manuel sonuç” ile öğretmen onayı verin.</div></div>`:`<div class="notice"><div><b>${score<db.threshold?"Tekrar sinyali oluşturuldu":"Başarı yeterli"}</b>${score<db.threshold?`%${db.threshold} eşiğinin altında olduğu için ${a.topic} konusu sonraki programda tekrar önceliği alacak.`:"Konu için otomatik tekrar sinyali oluşturulmadı."}</div></div>`}
   <div class="section"><h3>Zayıf Alanlar</h3>${(an.weaknesses||[]).map(x=>`<span class="course-chip">${x}</span>`).join("")||"—"}</div>
   <div class="section"><h3>Hata Türleri</h3>${(an.errorTypes||[]).map(x=>`<span class="course-chip">${typeof x==="string"?x:(x.type||x.label||JSON.stringify(x))}</span>`).join("")||"—"}</div>
   <div class="modal-actions"><button class="btn primary" onclick="closeModal();assignments()">Tamam</button></div>`;
 }catch(e){alert("Ödev analizi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent="Dosyayı Tara"}}
}

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.8.1 */

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.7.2 */
function q(id){return document.getElementById(id)}
function modal(html){const d=document.createElement("div");d.className="modalbg";d.id="modalbg";d.innerHTML=`<div class="modal">${html}</div>`;document.body.appendChild(d)}
window.closeModal=()=>document.getElementById("modalbg")?.remove()
window.resetDemo=()=>{db=structuredClone(seed);save();render()}

/* CELL:bootstrap */

/* CELL:bootstrap */
dashboard();
