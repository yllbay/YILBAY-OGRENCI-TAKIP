async function handleHomework(req,res){
  const body=await readJson(req,18*1024*1024);
  const {assignment,answerKey=null,resourceContext=null,studentFileSource="local"}=body;
  let studentFile;try{studentFile=await resolveStudentHomeworkFile(body)}catch(e){return json(res,400,{ok:false,error:e.message})}
  if(!integrationStatus().openai.configured)return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const expectedStudentPages=estimatePdfPageCount(studentFile.base64,studentFile.mimeType);
  const safeContext=resourceContext?{resourceId:resourceContext.resourceId||null,course:resourceContext.course||assignment?.course||"",unit:resourceContext.unit||"",topic:resourceContext.topic||assignment?.topic||"",level:resourceContext.level||"",title:resourceContext.title||assignment?.title||""}:null;
  const instructions=lunaHomeworkDirectInstruction()+"\nSadece geçerli ve KISA JSON döndür. Şema: {\"totalQuestions\":number,\"correct\":number,\"wrong\":number,\"blank\":number,\"uncertain\":number,\"scorePercent\":number,\"confidence\":number,\"needsTeacherReview\":boolean,\"correctQuestionNumbers\":[number],\"blankQuestionNumbers\":[number],\"uncertainQuestionNumbers\":[number],\"items\":[{\"question\":number,\"status\":\"wrong\",\"studentAnswer\":\"string|null\",\"correctAnswer\":\"string|null\",\"approach\":\"string|null\",\"stepsSummary\":[\"string\"],\"firstErrorStep\":\"string|null\",\"errorCategory\":\"conceptual|arithmetic|attention|method|incomplete|uncertain\",\"conceptualIssue\":\"string|null\",\"arithmeticIssue\":\"string|null\",\"attentionIssue\":\"string|null\",\"methodQuality\":\"efficient|acceptable|inefficient|incorrect|uncertain\",\"unnecessarySteps\":[\"string\"],\"missingSteps\":[\"string\"],\"betterApproach\":\"string|null\",\"learningObjective\":\"string|null\",\"solutionConfidence\":number,\"note\":\"string|null\"}],\"reasoningProfile\":{\"strengths\":[\"string\"],\"recurringErrors\":[\"string\"],\"conceptualGaps\":[\"string\"],\"proceduralGaps\":[\"string\"],\"attentionPatterns\":[\"string\"],\"recommendedActions\":[\"string\"],\"summary\":\"string\"},\"summary\":\"string\",\"answerKeyFound\":boolean,\"answerKeySource\":\"manual|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none\",\"answerKeyOriginDocument\":\"manual|student_pdf|ambiguous|none\",\"answerKeyConfidence\":number,\"answerKeyEvidence\":\"string\",\"analyzedStudentPages\":[number]}";
  const meta={assignment:{id:assignment?.id||null,course:assignment?.course||"",topic:assignment?.topic||"",title:assignment?.title||""},resourceContext:safeContext,manualAnswerKey:answerKey||null};
  const content=[{type:"input_text",text:JSON.stringify(meta)},{type:"input_text",text:"ÖĞRENCİ ÖDEV DOSYASI. Tüm sayfaları doğrudan Luna Vision ile analiz et. Beklenen fiziksel sayfa sayısı: "+(expectedStudentPages||"bilinmiyor")+". Doğru ve boş sorular için açıklama üretme; yalnız yanlışları ayrıntılandır."},{type:"input_file",filename:studentFile.fileName,file_data:"data:"+studentFile.mimeType+";base64,"+studentFile.base64}];
  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"low"});
  let parsed=normalizeHomeworkAnalysis(parseJsonText(ai.text));
  parsed.correctQuestionNumbers=normalizeQuestionNumberList(parsed.correctQuestionNumbers);
  parsed.blankQuestionNumbers=normalizeQuestionNumberList(parsed.blankQuestionNumbers);
  parsed.uncertainQuestionNumbers=normalizeQuestionNumberList(parsed.uncertainQuestionNumbers);
  parsed.items=Array.isArray(parsed.items)?parsed.items.filter(x=>String(x?.status||"wrong")==="wrong").slice(0,200):[];
  parsed=validateLunaDirectAnswerKey(parsed,answerKey);
  parsed=validateHomeworkPageCoverage(parsed,expectedStudentPages,0);
  parsed=validateLunaQuestionAccounting(parsed);
  parsed=deriveHomeworkReviewReasons(parsed);
  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  parsed.studentFileSource=studentFileSource;parsed.studentFileDriveUsed=!!studentFile.driveUsed;parsed.analysisArchitecture="direct_luna_wrong_only";
  writeHomeworkDiagnostic(parsed,cost,assignment);
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});
}

