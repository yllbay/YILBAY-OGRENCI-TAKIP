async function handleHomework(req,res){
  const totalStarted=Date.now(),body=await readJson(req,18*1024*1024);
  const {assignment,answerKey=null,resourceContext=null,studentFileSource="local"}=body;
  let studentFile;try{studentFile=await resolveStudentHomeworkFile(body)}catch(e){return json(res,400,{ok:false,error:e.message})}
  if(!integrationStatus().openai.configured)return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const expectedStudentPages=estimatePdfPageCount(studentFile.base64,studentFile.mimeType);
  const safeContext=resourceContext?{resourceId:resourceContext.resourceId||null,course:resourceContext.course||assignment?.course||"",unit:resourceContext.unit||"",topic:resourceContext.topic||assignment?.topic||"",level:resourceContext.level||"",title:resourceContext.title||assignment?.title||""}:null;
  const meta={assignment:{id:assignment?.id||null,course:assignment?.course||"",topic:assignment?.topic||"",title:assignment?.title||""},resourceContext:safeContext,manualAnswerKey:answerKey||null};
  const firstStarted=Date.now();
  const firstContent=[{type:"input_text",text:JSON.stringify(meta)},{type:"input_text",text:"BİRİNCİ GEÇİŞ: Tüm sayfaları tara; bölüm/test ve soru kimliklerini koru. Sadece doğru/yanlış/boş/belirsiz sınıflaması yap. Yanlış çözüm ayrıntısını bu geçişte üretme."},{type:"input_file",filename:studentFile.fileName,file_data:"data:"+studentFile.mimeType+";base64,"+studentFile.base64}];
  const firstAi=await openaiRequest({instructions:lunaHomeworkDirectInstruction()+"\nSadece geçerli ve KISA JSON döndür. Şema: {\"confidence\":number,\"needsTeacherReview\":boolean,\"correctQuestions\":[{\"sectionKey\":\"string\",\"section\":\"string\",\"page\":number,\"printedNumber\":number}],\"blankQuestions\":[aynı kimlik],\"uncertainQuestions\":[aynı kimlik],\"items\":[{\"sectionKey\":\"string\",\"section\":\"string\",\"page\":number,\"printedNumber\":number,\"status\":\"wrong\"}],\"reasoningProfile\":{\"strengths\":[],\"recurringErrors\":[],\"conceptualGaps\":[],\"proceduralGaps\":[],\"attentionPatterns\":[],\"recommendedActions\":[],\"summary\":\"\"},\"summary\":\"string\",\"answerKeyFound\":boolean,\"answerKeySource\":\"manual|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none\",\"answerKeyOriginDocument\":\"manual|student_pdf|ambiguous|none\",\"answerKeyConfidence\":number,\"answerKeyEvidence\":\"string\",\"analyzedStudentPages\":[number]}",input:[{role:"user",content:firstContent}],reasoning:"low"});
  const firstPassMs=Date.now()-firstStarted;
  let parsed=normalizeHomeworkAnalysis(parseJsonText(firstAi.text));
  parsed=finalizeHomeworkQuestionSets(parsed);
  parsed=validateLunaDirectAnswerKey(parsed,answerKey);
  parsed=validateHomeworkPageCoverage(parsed,expectedStudentPages,0);
  parsed=validateLunaQuestionAccounting(parsed);
  parsed=deriveHomeworkReviewReasons(parsed);
  const firstCost=appendUsage("homework_scan",firstAi.model,firstAi.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  const targets=homeworkMathVerificationTargets(parsed);
  let secondAi=null,secondCost=null,secondPassMs=0;
  if(targets.length){
    const secondStarted=Date.now(),targetMeta=targets.map(q=>({sectionKey:q.sectionKey,section:q.section,page:q.page,printedNumber:q.printedNumber,questionId:q.questionId}));
    const secondContent=[{type:"input_text",text:JSON.stringify({targets:targetMeta,manualAnswerKey:answerKey||null})},{type:"input_text",text:"İKİNCİ GEÇİŞ: Yalnız targets listesindeki soruları PDF içinde yeniden bul. Önce el yazısı matematik satırlarını ve sembolleri transkribe et, sonra işlemleri doğrula."},{type:"input_file",filename:studentFile.fileName,file_data:"data:"+studentFile.mimeType+";base64,"+studentFile.base64}];
    secondAi=await openaiRequest({instructions:homeworkMathVerificationInstruction()+"\nYalnız JSON: {\"reviews\":[{\"sectionKey\":\"string\",\"section\":\"string\",\"page\":number,\"printedNumber\":number,\"finalStatus\":\"correct|wrong|blank|uncertain\",\"transcriptionLines\":[\"string\"],\"symbolConfidence\":number,\"studentAnswer\":\"string|null\",\"correctAnswer\":\"string|null\",\"approach\":\"string|null\",\"stepsSummary\":[\"string\"],\"firstErrorStep\":\"string|null\",\"errorCategory\":\"conceptual|arithmetic|attention|method|incomplete|uncertain\",\"conceptualIssue\":\"string|null\",\"arithmeticIssue\":\"string|null\",\"attentionIssue\":\"string|null\",\"methodQuality\":\"efficient|acceptable|inefficient|incorrect|uncertain\",\"unnecessarySteps\":[\"string\"],\"missingSteps\":[\"string\"],\"betterApproach\":\"string|null\",\"learningObjective\":\"string|null\",\"solutionConfidence\":number,\"note\":\"string|null\"}]}",input:[{role:"user",content:secondContent}],reasoning:"low"});
    secondPassMs=Date.now()-secondStarted;
    const secondParsed=parseJsonText(secondAi.text);
    parsed=applyHomeworkMathVerification(parsed,secondParsed.reviews);
    parsed=validateLunaQuestionAccounting(parsed);
    parsed=deriveHomeworkReviewReasons(parsed);
    secondCost=appendUsage("homework_math_verify",secondAi.model,secondAi.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null,targetCount:targets.length});
  }else{parsed={...parsed,mathVerificationTargetCount:0,mathVerificationReviewedCount:0,mathVerificationLowConfidenceCount:0,mathVerificationComplete:true,mathVerificationUsed:false}}
  const totalMs=Date.now()-totalStarted,cost={try:Number(firstCost?.try||0)+Number(secondCost?.try||0),usd:Number(firstCost?.usd||0)+Number(secondCost?.usd||0),firstPass:firstCost,secondPass:secondCost};
  parsed.studentFileSource=studentFileSource;parsed.studentFileDriveUsed=!!studentFile.driveUsed;parsed.analysisArchitecture="two_pass_luna_math_verification";parsed.firstPassMs=firstPassMs;parsed.secondPassMs=secondPassMs;parsed.totalAnalysisMs=totalMs;parsed.firstPassCostTry=Number(firstCost?.try||0);parsed.secondPassCostTry=Number(secondCost?.try||0);
  writeHomeworkDiagnostic(parsed,cost,assignment);
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:{firstPass:firstAi.data?.usage||null,secondPass:secondAi?.data?.usage||null},cost});
}

