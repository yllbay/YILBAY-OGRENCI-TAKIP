window.approveHomeworkAnalysis=(assignmentId,analysisId)=>{
 const a=db.assignments.find(x=>x.id===assignmentId),an=db.homeworkAnalyses.find(x=>x.id===analysisId);if(!a||!an)return;
 const score=Math.max(0,Math.min(100,Number(q("teacherScore").value)));
 an.teacherReviewed=true;an.teacherReviewedAt=new Date().toISOString();an.teacherScore=score;an.teacherNote=q("teacherReviewNote").value.trim();
 a.status="Tamamlandı";a.completedAt=new Date().toISOString().slice(0,10);a.score=score;a.teacherReviewed=true;
 const existing=db.results.find(r=>r.assignmentId===a.id);
 if(existing){existing.score=score;existing.kind="AI Ödev Analizi · Öğretmen Onaylı";existing.date=a.completedAt}
 else db.results.push({id:Date.now(),studentId:a.studentId,kind:"AI Ödev Analizi · Öğretmen Onaylı",course:a.course,topic:a.topic,score,date:a.completedAt,assignmentId:a.id});
 db.repeatSignals=db.repeatSignals.filter(r=>r.assignmentId!==a.id||r.status!=="Bekliyor");
 if(score<db.threshold)db.repeatSignals.push({id:Date.now()+1,studentId:a.studentId,assignmentId:a.id,course:a.course,topic:a.topic,score,threshold:db.threshold,status:"Bekliyor",createdAt:new Date().toISOString(),source:"teacher-review"});
 save();closeModal();assignments();
}
