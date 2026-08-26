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

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.9.0 */

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.7.2 */
