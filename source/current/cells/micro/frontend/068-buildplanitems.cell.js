function buildPlanItems(s){
 const latest={};
 db.results.filter(r=>r.studentId===s.id).forEach(r=>{const k=r.course+"|||"+r.topic;if(!latest[k]||String(r.date)>=String(latest[k].date))latest[k]=r});
 const repeats=Object.values(latest).filter(r=>r.score<db.threshold).map(r=>{
   const wanted=s.levels?.[r.course]||"Orta";
   const res=db.resources.find(x=>x.course===r.course&&x.topic===r.topic&&x.level===wanted)||db.resources.find(x=>x.course===r.course&&x.topic===r.topic);
   const exam=db.exams.find(x=>x.course===r.course&&x.topic===r.topic);
   return {type:"Tekrar",course:r.course,topic:r.topic,level:wanted,resource:res?.title||"Uygun kaynak ekleyin",exam:exam?.title||"—",reason:`Son başarı %${r.score}`,priority:0}
 });
 const pending=db.assignments.filter(a=>a.studentId===s.id&&a.status!=="Tamamlandı").map(a=>({
   type:"Atama",course:a.course,topic:a.topic,level:s.levels?.[a.course]||"Orta",
   resource:a.kind==="PDF Kaynak"?a.title:"—",exam:a.kind==="Online Sınav"?a.title:"—",
   reason:"Bekleyen atama",priority:1
 }));
 const map=new Map();
 [...repeats,...pending].forEach(x=>{const k=x.type+"|||"+x.course+"|||"+x.topic+"|||"+x.resource+"|||"+x.exam;if(!map.has(k))map.set(k,x)});
 return [...map.values()].sort((a,b)=>a.priority-b.priority||a.course.localeCompare(b.course));
}


