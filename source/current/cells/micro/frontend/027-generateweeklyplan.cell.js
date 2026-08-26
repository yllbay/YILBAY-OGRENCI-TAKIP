

function generateWeeklyPlan(){
 const s=db.students.find(x=>x.id===selectedStudentId);if(!s)return;
 const items=buildPlanItems(s);
 const days=Object.fromEntries(DAY_NAMES.map(d=>[d,[]]));
 items.forEach((item,i)=>days[DAY_NAMES[i%7]].push(item));
 db.weeklyPlans[String(s.id)]={generatedAt:new Date().toISOString(),days};
 save();program()
}
