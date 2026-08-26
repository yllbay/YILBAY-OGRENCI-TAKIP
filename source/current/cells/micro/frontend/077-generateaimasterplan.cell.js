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

/* CELL:110-youtube | layer:frontend | generated-from:v0.11.0 */

/* CELL:110-youtube | layer:frontend | generated-from:v0.7.2 */
