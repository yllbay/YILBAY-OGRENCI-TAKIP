window.findTopicVideo=async(course,topic)=>{
 try{
  const key=course+"|||"+topic;
  modal(`<h2>Konu Anlatım Videosu</h2><div id="videoResults"><div class="muted">YouTube aranıyor…</div></div><div class="modal-actions"><button class="btn ghost" onclick="closeModal()">Kapat</button></div>`);
  const data=await apiJson("/api/youtube/search",{query:`${course} ${topic} konu anlatımı YKS TYT AYT`,maxResults:5});
  db.videoSuggestions[key]=data.videos;save();
  q("videoResults").innerHTML=data.videos.length?`<div class="video-list">${data.videos.map((v,i)=>`<a class="video-row" href="${v.url}" target="_blank" rel="noopener"><div class="video-rank">${i+1}</div><div><div class="cell-title">${v.title}</div><div class="cell-sub">${v.channelTitle}</div></div></a>`).join("")}</div>`:emptyState("Video bulunamadı","Arama sorgusunu veya API ayarını kontrol edin.")
 }catch(e){if(q("videoResults"))q("videoResults").innerHTML=`<div class="notice error">${e.message}</div>`;else alert(e.message)}
}

/* CELL:120-ai-homework | layer:frontend | generated-from:v0.10.5 */

/* CELL:120-ai-homework | layer:frontend | generated-from:v0.7.2 */
