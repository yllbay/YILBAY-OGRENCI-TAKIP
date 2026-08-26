/* CELL:40-academic-planner | layer:backend | generated-from:v0.7.2 */
function flattenCurriculum(curriculum,courses){
  const rows=[];
  for(const course of courses||[]){
    const units=curriculum?.[course]||{};
    for(const [unit,topics] of Object.entries(units)){
      for(const topic of topics||[]) rows.push({course,unit,topic});
    }
  }
  return rows;
}
function deterministicPlan(student,curriculum,resources=[]){
  const topics=flattenCurriculum(curriculum,student.courses);
  const start=new Date(student.registeredAt||new Date().toISOString().slice(0,10));
  const end=new Date(student.courseEndDate||start);
  const weekMs=7*864e5;
  const weekCount=Math.max(1,Math.floor((end-start)/weekMs)+1);
  const studyDays=Math.max(1,Math.min(7,Number(student.weeklyStudyDays||6)));
  const dailyMinutes=Math.max(30,Number(student.dailyMinutes||120));
  const weeklyCapacity=studyDays*dailyMinutes;
  const levelOrder=["Başlangıç","Kolay","Orta","Orta-Zor","Zor","İleri"];
  function pickResource(course,topic,wanted){
    const same=resources.filter(r=>r.course===course&&r.topic===topic);
    if(!same.length) return null;
    const wi=Math.max(0,levelOrder.indexOf(wanted));
    same.sort((a,b)=>{
      const ai=levelOrder.indexOf(a.level),bi=levelOrder.indexOf(b.level);
      const ad=ai<0?99:Math.abs(ai-wi),bd=bi<0?99:Math.abs(bi-wi);
      return ad-bd;
    });
    return same[0];
  }
  const weeks=Array.from({length:weekCount},(_,i)=>({week:i+1,startDate:new Date(start.getTime()+i*weekMs).toISOString().slice(0,10),capacityMinutes:weeklyCapacity,plannedMinutes:0,items:[]}));
  const baseTopicMinutes=Math.min(120,Math.max(35,Math.round(dailyMinutes*0.55)));
  let wi=0,overflowTopics=[];
  for(const x of topics){
    const level=student.levels?.[x.course]||"Orta";
    const res=pickResource(x.course,x.topic,level);
    const estimatedMinutes=baseTopicMinutes;
    while(wi<weeks.length && weeks[wi].plannedMinutes+estimatedMinutes>weeks[wi].capacityMinutes) wi++;
    if(wi>=weeks.length){overflowTopics.push({...x,estimatedMinutes});continue}
    weeks[wi].items.push({...x,type:"Yeni Konu",priority:"normal",resourceId:res?.id??null,resourceTitle:res?.title||null,resourceLevel:res?.level||null,studentLevel:level,estimatedMinutes});
    weeks[wi].plannedMinutes+=estimatedMinutes;
  }
  const totalCapacityMinutes=weekCount*weeklyCapacity;
  const requiredMinutes=topics.length*baseTopicMinutes;
  return {mode:"deterministic",weeks,totalTopics:topics.length,weeklyCapacityMinutes:weeklyCapacity,totalCapacityMinutes,requiredMinutes,overload:overflowTopics.length>0,overflowCount:overflowTopics.length,overflowTopics};
}
async function handleAiPlan(req,res){
  const body=await readJson(req,2*1024*1024);
  const {student,curriculum,results=[],resources=[]}=body;
  if(!student) return json(res,400,{ok:false,error:"Öğrenci verisi gerekli"});
  const fallback=deterministicPlan(student,curriculum||{},resources);
  if(!integrationStatus().openai.configured) return json(res,200,{ok:true,usedAi:false,plan:fallback,warning:"OpenAI API anahtarı ayarlı değil; deterministik plan üretildi."});
  const topics=flattenCurriculum(curriculum,student.courses);
  const prompt={
    student:{
      id:student.id,name:student.name,grade:student.grade,target:student.target,
      registeredAt:student.registeredAt,courseEndDate:student.courseEndDate,
      weeklyStudyDays:student.weeklyStudyDays,dailyMinutes:student.dailyMinutes,
      courses:student.courses,levels:student.levels
    },
    topics,
    recentResults:results.slice(-80),
    resources:resources.map(r=>({id:r.id,course:r.course,topic:r.topic,level:r.level,title:r.title})).slice(0,300)
  };
  const instructions=`Sen bir akademik koçluk planlama motorusun. Görevin öğrencinin kayıt tarihi ile kurs bitiş tarihi arasındaki haftalara tüm ünite/alt konu başlıklarını yetişecek şekilde dağıtmaktır.
Kurallar:
- Öğrencinin haftalık çalışma gününü ve günlük dakika sınırını aşma.
- Ön koşullu konuları mümkün olduğunca pedagojik sırada tut.
- Öğrencinin ders bazlı seviyesini dikkate al.
- Sonuçlarda başarı eşiğinin altında kalmış konular varsa erken haftalara "Tekrar" olarak ekle.
- Kaynak listesinde konu ve seviyeye uygun PDF varsa resourceId alanına koy; yoksa null.
- Aynı haftayı aşırı yükleme.
- Sadece geçerli JSON döndür.
Şema:
{"weeks":[{"week":1,"startDate":"YYYY-MM-DD","items":[{"course":"...","unit":"...","topic":"...","type":"Yeni Konu|Tekrar","priority":"high|normal","resourceId":number|null,"estimatedMinutes":number,"reason":"kısa gerekçe"}]}],"totalTopics":number,"notes":["..."]}`;
  const ai=await openaiRequest({instructions,input:JSON.stringify(prompt),reasoning:"medium"});
  const parsed=parseJsonText(ai.text);
  const cost=appendUsage("plan",ai.model,ai.data?.usage||{}, {studentId:student.id});
  return json(res,200,{ok:true,usedAi:true,plan:{mode:"ai",...parsed},usage:ai.data?.usage||null,cost});
}
