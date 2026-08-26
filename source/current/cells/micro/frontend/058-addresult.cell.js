window.addResult=()=>{const [course,topic]=q("xtopic").value.split("|||"),score=Math.max(0,Math.min(100,Number(q("xscore").value)));db.results.push({id:Date.now(),studentId:Number(q("xstudent").value),kind:q("xkind").value,course,topic,score,date:new Date().toISOString().slice(0,10)});save();closeModal();results()}

/* CELL:70-planner | layer:frontend | generated-from:v0.9.2 */

/* CELL:70-planner | layer:frontend | generated-from:v0.7.2 */
