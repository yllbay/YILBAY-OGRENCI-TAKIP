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


