window.addExam=()=>{const [course,topic]=q("etopic").value.split("|||");db.exams.push({id:Date.now(),course,topic,title:q("etitle").value||topic+" Online Test",url:q("eurl").value});save();closeModal();exams()}

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.10.1 */

/* CELL:60-assignments-results | layer:frontend | generated-from:v0.7.2 */
