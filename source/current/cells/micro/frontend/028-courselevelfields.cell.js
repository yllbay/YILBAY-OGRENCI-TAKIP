function courseLevelFields(selected=[],levels={}){
 return Object.keys(db.curriculum).map(c=>`<div class="item"><label><input type="checkbox" class="coursecheck" value="${c}" ${selected.includes(c)?"checked":""}> <b>${c}</b></label>
 <select class="courselevel" data-course="${c}"><option>Başlangıç</option><option>Kolay</option><option ${levels[c]==="Orta"?"selected":""}>Orta</option><option ${levels[c]==="Orta-Zor"?"selected":""}>Orta-Zor</option><option ${levels[c]==="Zor"?"selected":""}>Zor</option><option ${levels[c]==="İleri"?"selected":""}>İleri</option></select></div>`).join("")
}
