const seed={
 students:[{id:1,name:"Bilgehan Özdurak",grade:"12",target:"YKS",registeredAt:"2026-08-26",courseEndDate:"2027-06-01",weeklyStudyDays:6,dailyMinutes:120,aiAutoPlan:true,courses:["TYT Matematik","Problemler","Türkçe"],levels:{"TYT Matematik":"Orta","Problemler":"Orta-Zor","Türkçe":"Orta"}}],
 curriculum:{
   "TYT Matematik":{"Temel Matematik":["Temel Kavramlar","Bölme-Bölünebilme","Rasyonel Sayılar","1. Derece Denklemler","Basit Eşitsizlikler","Mutlak Değer"]},
   "Problemler":{"Problemler":["Sayı Problemleri","Kesir Problemleri","Yaş Problemleri"]},
   "Türkçe":{"Paragraf":["Paragrafta Konu","Paragrafta Başlık","Ana Düşünce"],"Dil Bilgisi":["Yazım Kuralları","Ses Bilgisi"]}
 },
 resources:[
  {id:1,type:"PDF",course:"TYT Matematik",topic:"Mutlak Değer",level:"Orta",title:"Mutlak Değer Ödev 01",url:""},
  {id:2,type:"PDF",course:"Problemler",topic:"Sayı Problemleri",level:"Orta-Zor",title:"Sayı Problemleri Ödev 01",url:""}
 ],
 exams:[
  {id:1,course:"TYT Matematik",topic:"Mutlak Değer",title:"Mutlak Değer Online Test",url:"https://example.com"}
 ],
 results:[
  {id:1,studentId:1,kind:"Ödev",course:"TYT Matematik",topic:"Mutlak Değer",score:58,date:"2026-08-25"},
  {id:2,studentId:1,kind:"Online Sınav",course:"TYT Matematik",topic:"Basit Eşitsizlikler",score:74,date:"2026-08-25"}
 ],
 threshold:70
};


