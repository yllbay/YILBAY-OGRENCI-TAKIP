function lunaHomeworkDirectInstruction(){return `LUNA MALİYET-OPTİMİZE ÖDEV ANALİZ PROTOKOLÜ:
Yüklenen öğrenci PDF/görselinin tamamını doğrudan analiz et; ilk sayfada durma ve tüm fiziksel sayfaları sırayla tara.
Önce her basılı soruyu yalnız correct|wrong|blank|uncertain olarak sınıflandır. Soru kimliği yalnız basılı/orijinal soru numarasıdır.
DOĞRU sorular için çözüm açıklaması, yaklaşım, adım analizi, pedagojik yorum veya övgü üretme. Yalnız correctQuestionNumbers listesine soru numarasını yaz.
BOŞ sorular için neden tahmini veya çözüm analizi üretme. Yalnız blankQuestionNumbers listesine soru numarasını yaz.
UNCERTAIN/okunamayan sorular için tahmin yapma. Yalnız uncertainQuestionNumbers listesine soru numarasını yaz ve gerekiyorsa needsTeacherReview=true yap.
YALNIZ WRONG sorular için items dizisinde ayrıntılı analiz üret: studentAnswer, correctAnswer, approach, stepsSummary, firstErrorStep, errorCategory, conceptualIssue, arithmeticIssue, attentionIssue, methodQuality, unnecessarySteps, missingSteps, betterApproach, learningObjective, solutionConfidence ve kısa note.
El yazısında ilk yanlış adımı özellikle bul. Bu sürümün hedefi gerçek yanlışların nedenini anlamaktır.
PDF içinde güvenilir basılı cevap anahtarı varsa yerini answerKeyEvidence ile belirt. Manuel cevap anahtarı verilmişse onu kullan. Güvenilir cevap anahtarı yoksa doğru/yanlış uydurma; ilgili soruları uncertain yap.
reasoningProfile yalnız WRONG sorulardan türetilsin: recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve kısa summary. Gereksiz uzun metin üretme. strengths yalnız yanlış analizinden açıkça çıkarılabiliyorsa kısa olsun.
`}
