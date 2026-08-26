async function handleHomework(req,res){
  const body=await readJson(req,18*1024*1024);
  const {assignment,answerKey=null,resourceContext=null,studentFileSource="local"}=body;
  let studentFile;try{studentFile=await resolveStudentHomeworkFile(body)}catch(e){return json(res,400,{ok:false,error:e.message})}
  const {base64:fileData,mimeType,fileName}=studentFile;
  if(!integrationStatus().openai.configured) return json(res,400,{ok:false,error:"Ödev analizi için OpenAI API anahtarı gerekli"});
  const answerKeySearch=homeworkAnswerKeySearchInstruction();
  const reasoningInstruction=homeworkReasoningInstruction();
  const assignmentScopeInstruction=homeworkAssignmentScopeInstruction();
  const expectedStudentPages=estimatePdfPageCount(fileData,mimeType);
  let expectedSourcePages=0;
  const instructions=`Sen bir öğrenci ödevi değerlendirme motorusun. Yüklenen PDF/görselin SADECE İLK SAYFASINI DEĞİL TÜM SAYFALARINI 1. sayfadan son sayfaya kadar sırayla incele. Hiçbir sayfayı atlama. Öğrencinin işaretlerini, boş bıraktığı soruları ve mümkünse çözüm yollarını tüm belge boyunca incele.
${answerKeySearch}
${reasoningInstruction}
${assignmentScopeInstruction}
Cevap anahtarı kanıtı olmadan doğru/yanlış durumunu kesinmiş gibi uydurma.
Yanlış/boş/doğru sayısını, başarı yüzdesini ve hata türlerini çıkar. Öğrencinin çözüm yolu görünüyorsa temel kavramsal hataları kısa şekilde sınıflandır.
Kesin göremediğin işaret veya çözüm için tahmin yürütme. Soruların/işaretlerin yeterli kısmı okunamıyorsa needsTeacherReview=true yap.
confidence 0 ile 1 arasında olmalı. confidence 0.65 altındaysa sonuç öğretmen onayı gerektirmelidir. Her öğrenci PDF sayfasını gerçekten inceledikten sonra analyzedStudentPages alanına sayfa numaralarını tek tek yaz. Kaynak PDF verildiyse cevap anahtarı araması dahil tüm gerekli kaynak sayfalarını incele ve analyzedSourcePages alanına yaz.
Sadece JSON döndür:
{"assignmentMatchFound":boolean,"assignmentMatchConfidence":number,"assignmentMatchEvidence":"string","matchedTestName":"string|null","matchedQuestionNumbers":[number],"totalQuestions":number,"correct":number,"wrong":number,"blank":number,"scorePercent":number,"confidence":number,"items":[{"question":number,"status":"correct|wrong|blank|uncertain","studentAnswer":"string|null","correctAnswer":"string|null","approach":"string|null","stepsSummary":["string"],"firstErrorStep":"string|null","errorCategory":"conceptual|arithmetic|attention|method|incomplete|none|uncertain","conceptualIssue":"string|null","arithmeticIssue":"string|null","attentionIssue":"string|null","methodQuality":"efficient|acceptable|inefficient|incorrect|uncertain","unnecessarySteps":["string"],"missingSteps":["string"],"betterApproach":"string|null","learningObjective":"string|null","solutionConfidence":number,"errorType":"string|null","note":"string|null"}],"reasoningProfile":{"strengths":["string"],"recurringErrors":["string"],"conceptualGaps":["string"],"proceduralGaps":["string"],"attentionPatterns":["string"],"recommendedActions":["string"],"summary":"string"},"weaknesses":["..."],"recommendRepeat":boolean,"summary":"...","answerKeyFound":boolean,"answerKeySource":"manual|external_drive|embedded_same_page|embedded_adjacent_page|embedded_end_pages|ambiguous|none","answerKeyConfidence":number,"answerKeyEvidence":"kısa konum/eşleşme açıklaması","answerKeyTestName":"string|null","studentDocumentPageCount":number,"analyzedStudentPages":[number],"sourceDocumentPageCount":number,"analyzedSourcePages":[number]}`;
  const content=[{type:"input_text",text:JSON.stringify({assignment,answerKey,resourceContext})}];
  if(studentFileSource==="drive"&&resourceContext?.driveFileId){const src=await driveDownloadAnalysisFile(resourceContext.driveFileId);expectedSourcePages=estimatePdfPageCount(src.base64,src.mimeType);content.push({type:"input_text",text:`KAYNAK PDF - tüm gerekli sayfaları incele. Beklenen sayfa sayısı: ${expectedSourcePages||"bilinmiyor"}`},{type:"input_file",filename:"kaynak.pdf",file_data:`data:${src.mimeType};base64,${src.base64}`})}
  if(studentFileSource==="drive"&&resourceContext?.answerKeyDriveFileId){const key=await driveDownloadAnalysisFile(resourceContext.answerKeyDriveFileId);content.push({type:"input_text",text:"CEVAP ANAHTARI - kesin referans olarak kullan"},{type:"input_file",filename:"cevap_anahtari.pdf",file_data:`data:${key.mimeType};base64,${key.base64}`})}
  content.push({type:"input_text",text:`ÖĞRENCİ ÇÖZÜM DOSYASI - TÜM SAYFALARI tara. Beklenen sayfa sayısı: ${expectedStudentPages||"bilinmiyor"}. İlk sayfada durma.`},{type:"input_file",filename:fileName,file_data:`data:${mimeType};base64,${fileData}`});
  const ai=await openaiRequest({instructions,input:[{role:"user",content}],reasoning:"medium"});
  const parsed=deriveHomeworkReviewReasons(validateHomeworkQuestionAccounting(validateHomeworkAssignmentScope(validateHomeworkPageCoverage(validateHomeworkAnswerKeyEvidence(validateHomeworkQuestionCount(normalizeHomeworkAnalysis(parseJsonText(ai.text)),resourceContext?.questionCount),answerKey,resourceContext),expectedStudentPages,expectedSourcePages),resourceContext?.questionCount)));
  const cost=appendUsage("homework_analysis",ai.model,ai.data?.usage||{}, {studentId:assignment?.studentId||null,assignmentId:assignment?.id||null});
  parsed.studentFileSource=studentFileSource;parsed.studentFileDriveUsed=!!studentFile.driveUsed;
  writeHomeworkDiagnostic(parsed,cost,assignment);
  return json(res,200,{ok:true,analysis:parsed,autoFinalize:parsed.autoFinalize,usage:ai.data?.usage||null,cost});
}

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */
