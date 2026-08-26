function lunaHomeworkDirectInstruction(){return `LUNA MALİYET-OPTİMİZE ÖDEV ANALİZ PROTOKOLÜ:
Yüklenen öğrenci PDF/görselinin tamamını doğrudan analiz et; ilk sayfada durma ve tüm fiziksel sayfaları sırayla tara.
ÖNCE PDF'deki bölüm/test başlıklarını belirle. Soru numaraları yeni bölüm/testte 1'den yeniden başlayabilir. Aynı basılı soru numarası farklı bölüm/testlerde FARKLI sorudur.
Soru kimliği kesinlikle yalnız basılı sayı değildir. Her fiziksel soru için sectionKey + printedNumber kullan. sectionKey aynı bölüm/test boyunca sabit, kısa ve benzersiz olsun. Örnek: sayi-problemleri:1, kesir-problemleri:1 ve bos-dolu-problemleri:1 üç ayrı sorudur. Başlık yoksa fallback olarak page<sayfa>:q<basılıNo> kullan. Kesme/görünme sırasını kimlik yapma.
DOĞRU sorular için yalnız {sectionKey,section,page,printedNumber} kaydını correctQuestions listesine yaz; çözüm açıklaması üretme.
BOŞ sorular için yalnız aynı kimlik alanlarını blankQuestions listesine yaz; neden tahmini yapma.
UNCERTAIN sorular için yalnız aynı kimlik alanlarını uncertainQuestions listesine yaz; tahmin yapma.
YALNIZ WRONG sorular için items içinde kimlik alanlarıyla birlikte studentAnswer, correctAnswer, approach, stepsSummary, firstErrorStep, errorCategory, conceptualIssue, arithmeticIssue, attentionIssue, methodQuality, unnecessarySteps, missingSteps, betterApproach, learningObjective, solutionConfidence ve kısa note üret.
El yazısında ilk yanlış adımı özellikle bul. PDF içinde güvenilir basılı cevap anahtarı varsa yerini answerKeyEvidence ile belirt. Güvenilir anahtar yoksa doğru/yanlış uydurma; uncertain yap.
reasoningProfile yalnız WRONG sorulardan türetilsin ve kısa olsun.
`}
