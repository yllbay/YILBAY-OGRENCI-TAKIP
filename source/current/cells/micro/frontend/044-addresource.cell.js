window.addResource=()=>{const [course,topic]=q("rtopic").value.split("|||");db.resources.push({id:Date.now(),type:"PDF",course,topic,level:q("rlevel").value,title:q("rtitle").value||topic+" Kaynak",url:q("rurl").value});save();closeModal();resources()}

/* CELL:50-exams | layer:frontend | generated-from:v0.9.2 */

/* CELL:50-exams | layer:frontend | generated-from:v0.7.2 */
