/* CELL:50-homework-vision | layer:backend | generated-from:v0.7.2 */
function normalizeHomeworkAnalysis(x={}){
  const clamp=(n,a,b)=>Math.max(a,Math.min(b,Number.isFinite(Number(n))?Number(n):a));
  const correct=Math.max(0,Math.round(Number(x.correct)||0));
  const wrong=Math.max(0,Math.round(Number(x.wrong)||0));
  const blank=Math.max(0,Math.round(Number(x.blank)||0));
  const total=Math.max(0,Math.round(Number(x.totalQuestions)||correct+wrong+blank));
  let score=Number(x.scorePercent);
  if(!Number.isFinite(score) && correct+wrong+blank>0) score=100*correct/(correct+wrong+blank);
  score=clamp(score,0,100);
  const confidence=clamp(x.confidence,0,1);
  const modelReview=!!x.needsTeacherReview;
  const reviewRequired=modelReview || confidence<0.65 || total===0;
  return {
    ...x,
    correct,wrong,blank,totalQuestions:total,
    scorePercent:Math.round(score*10)/10,
    confidence:Math.round(confidence*1000)/1000,
    needsTeacherReview:reviewRequired,
    autoFinalize:!reviewRequired,
    weaknesses:Array.isArray(x.weaknesses)?x.weaknesses.slice(0,20):[],
    errorTypes:Array.isArray(x.errorTypes)?x.errorTypes.slice(0,30):[],
    notes:Array.isArray(x.notes)?x.notes.slice(0,20):[]
  };
}
async function handleHomework(req,res){
  const body=await readJson(req,18*1024*1024);
  const {fileData,mimeType="application/pdf",fileName="odev.pdf",assignment,answerKey=null}=body;
  if(!fileData) return json(res,400,{ok:false,error:"Ödev dosyası gerekli"});
  if(!integrationStatus().openai.configured) return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun. Yüklenen PDF/görselde öğrencinin işaretlerini, boş bıraktığı soruları ve mümkünse çözüm yollarını incele.
Eğer cevap anahtarı sağlandıysa onu kesin referans olarak kullan. Cevap anahtarı yoksa yalnızca güvenle değerlendirebildiklerini puanla ve confidence değerini düşür.
Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.
Kesin göremediğin işaret veya çözüm için tahmin yürütme. Soruların/işaretlerin yeterli kısmı okunamıyorsa needsTeacherReview=true yap.
confidence 0 ile 1 arasında olmalı. confidence 0.65 altındaysa sonuç öğretmen onayı gerektirmelidir.
Sadece JSON döndür:
{"totalQuestions":number,"correct":number,"wrong":number,"blank":number,"scorePercent":number,"confidence":number,"items":[{"question":number,"status":"correct|wrong|blank|uncertain","studentAnswer":"string|null","correctAnswer":"string|null","errorType":"string|null","note":"string|null"}],"weaknesses":["..."],"recommendRepeat":boolean,"summary":"..."}`;
  const content=[
    {type:"input_text",text:JSON.stringify({assignment,answerKey})},
    {type:"input_file",filename:fileName,file_data:`data:${mimeType};base64,${fileData}`}
  ];
  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"medium"});
  const parsed=normalizeHomeworkAnalysis(parseJsonText(ai.text));
  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});
}
