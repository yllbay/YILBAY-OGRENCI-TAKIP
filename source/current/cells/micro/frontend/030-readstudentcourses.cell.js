function readStudentCourses(){
 const courses=[...document.querySelectorAll(".coursecheck:checked")].map(x=>x.value),levels={};
 courses.forEach(c=>{levels[c]=document.querySelector(`.courselevel[data-course="${c}"]`)?.value||"Orta"});
 return {courses,levels}
}
