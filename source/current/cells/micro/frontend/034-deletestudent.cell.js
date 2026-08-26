window.deleteStudent=id=>{if(!confirm("Öğrenci silinsin mi?"))return;db.students=db.students.filter(s=>s.id!==id);db.results=db.results.filter(r=>r.studentId!==id);save();students()}

