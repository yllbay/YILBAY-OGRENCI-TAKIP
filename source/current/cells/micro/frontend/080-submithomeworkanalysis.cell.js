window.submitHomeworkAnalysis=async id=>{
 const a=db.assignments.find(x=>x.id===id),studentFileSource=q("homeworkSource")?.value||"local",file=q("homeworkFile")?.files?.[0],studentDriveFileId=driveFileIdFromInput(q("homeworkDriveInput")?.value);if(!a)return;
 if(studentFileSource==="local"&&!file)return alert("Ödev dosyasını seçin");
 if(studentFileSource==="drive"&&!studentDriveFileId)return alert("Geçerli Drive dosya bağlantısı veya kimliği girin");
 if(file&&file.size>14*1024*1024)return alert("Bu sürümde dosya en fazla 14 MB olabilir.");
 const btn=document.querySelector(".modal-actions .btn.primary");if(btn){btn.disabled=true;btn.textContent="AI tarıyor…"}
 try{
  const fileData=studentFileSource==="local"?await fileToBase64(file):null,answerKey=q("answerKey").value.trim()||null,resourceContext=assignmentResourceContext(a);
  const data=await apiJson("/api/ai/analyze-homework",{studentFileSource,studentDriveFileId,fileData,mimeType:file?.type||"application/pdf",fileName:file?.name||"drive_odev.pdf",assignment:{id:a.id,studentId:a.studentId,course:a.course,topic:a.topic,title:a.title},answerKey,resourceContext});
  const an=data.analysis||{},score=Math.round(Number(an.scorePercent)||0),reviewRequired=!!an.needsTeacherReview||data.autoFinalize===false;
  db.homeworkAnalyses.push({id:Date.now(),assignmentId:a.id,studentId:a.studentId,course:a.course,topic:a.topic,date:new Date().toISOString().slice(0,10),fileName:file?.name||"Drive ödevi",fileSize:file?.size||0,mimeType:file?.type||"application/pdf",studentFileSource,costTry:Number(data.cost?.try||0),...an});
  a.completedAt=new Date().toISOString().slice(0,10);a.score=score;a.aiConfidence=Number(an.confidence||0);
  if(reviewRequired){
    a.status="Öğretmen Kontrolü";
  }else{
    a.status="Tamamlandı";
    db.results.push({id:Date.now()+1,studentId:a.studentId,kind:"AI Ödev Analizi",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});
    if(score<db.threshold&&!db.repeatSignals.some(r=>r.assignmentId===a.id&&r.status==="Bekliyor"))db.repeatSignals.push({id:Date.now()+2,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString()});
  }
  save();
  q("modalbg").querySelector(".modal").innerHTML=`<h2>${reviewRequired?"Öğretmen Kontrolü Gerekli":"Ödev Analizi Tamamlandı"}</h2><div class="result-hero"><div class="kpi">%${score}</div><div><div class="cell-title">${an.correct||0} doğru · ${an.wrong||0} yanlış · ${an.blank||0} boş</div><div class="cell-sub">Güven: %${Math.round((Number(an.confidence)||0)*100)} · Cevap anahtarı: ${homeworkAnswerKeySourceLabel(an.answerKeySource)} (%${Math.round((Number(an.answerKeyConfidence)||0)*100)})${data.cost?` · AI maliyeti ${Number(data.cost.try||0).toFixed(4)} TL`:""}</div></div></div>
   ${reviewRequired?`<div class="notice error"><div><b>Otomatik sonuç kesinleştirilmedi</b>${an.reviewReasons?.length?`Kontrol nedenleri: ${an.reviewReasons.join(", ")}. `:""}Bu analiz başarı sonuçlarına ve tekrar motoruna otomatik aktarılmadı. Atamalar ekranından “Manuel sonuç” ile öğretmen onayı verin.</div></div>`:`<div class="notice"><div><b>${score<db.threshold?"Tekrar sinyali oluşturuldu":"Başarı yeterli"}</b>${score<db.threshold?`%${db.threshold} eşiğinin altında olduğu için ${a.topic} konusu sonraki programda tekrar önceliği alacak.`:"Konu için otomatik tekrar sinyali oluşturulmadı."}</div></div>`}
   <div class="section"><h3>Atama Soru Kapsamı</h3><div class="cell-sub">Eşleşen soru sayısı: ${an.matchedQuestionCount||0}${an.matchedQuestionNumbers?.length?` · Basılı numaralar: ${an.matchedQuestionNumbers.join(", ")}`:""}<br>${an.assignmentMatchEvidence||"—"}</div></div>
   <div class="section"><h3>Sayfa Kapsamı</h3><div class="cell-sub">Taranan öğrenci sayfaları: ${(an.analyzedStudentPages||[]).join(", ")||"—"} / beklenen ${an.expectedStudentPages||"?"}${an.missingStudentPages?.length?` · Eksik: ${an.missingStudentPages.join(", ")}`:""}</div></div>
   <div class="section"><h3>Cevap Anahtarı Kanıtı</h3><div class="cell-sub">${an.answerKeyEvidence||"—"}</div></div>
   <div class="section"><h3>Çözüm Yaklaşımı ve Hatalar</h3>${(an.items||[]).map(x=>'<div class="card" style="margin:8px 0"><div class="cell-title">Soru '+(x.question||"?")+' · '+(x.status||"uncertain")+'</div><div class="cell-sub">Yaklaşım: '+(x.approach||"—")+'<br>İlk hata: '+(x.firstErrorStep||"—")+'<br>Hata sınıfı: '+(x.errorCategory||"—")+'<br>Daha iyi yaklaşım: '+(x.betterApproach||"—")+'<br>Kazanım: '+(x.learningObjective||"—")+'</div></div>').join("")||"—"}</div>
   <div class="section"><h3>Pedagojik Özet</h3><div class="cell-sub">${an.reasoningProfile?.summary||an.summary||"—"}</div></div>
   <div class="section"><h3>Zayıf Alanlar</h3>${(an.weaknesses||[]).map(x=>`<span class="course-chip">${x}</span>`).join("")||"—"}</div>
   <div class="section"><h3>Hata Türleri</h3>${(an.errorTypes||[]).map(x=>`<span class="course-chip">${typeof x==="string"?x:(x.type||x.label||JSON.stringify(x))}</span>`).join("")||"—"}</div>
   <div class="modal-actions"><button class="btn primary" onclick="closeModal();assignments()">Tamam</button></div>`;
 }catch(e){alert("Ödev analizi başarısız: "+e.message)}
 finally{if(btn){btn.disabled=false;btn.textContent="Dosyayı Tara"}}
}

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.10.4 */

/* CELL:130-ui-runtime | layer:frontend | generated-from:v0.7.2 */
