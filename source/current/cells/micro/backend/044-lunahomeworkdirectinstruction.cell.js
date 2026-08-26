function lunaHomeworkDirectInstruction(){return `LUNA DOĞRUDAN ÖDEV ANALİZ PROTOKOLÜ:
Yüklenen öğrenci PDF/görselinin tamamını doğrudan analiz et. Programın yerel tahminlerine güvenme; belgeyi kendin incele. İlk sayfada durma, tüm sayfaları sırayla tara.
Her basılı soru için soru numarasını, öğrencinin cevabını, doğru cevabı yalnız güvenilir cevap anahtarı varsa, correct|wrong|blank|uncertain durumunu ve el yazısı çözümünü değerlendir.
El yazısında öğrencinin yaklaşımını, görülen çözüm adımlarını, ilk hata adımını, kavramsal/işlem/dikkat/yöntem/eksik çözüm hatasını, gereksiz ve eksik adımları, yöntem kalitesini, daha iyi yaklaşımı ve tekrar edilmesi gereken kazanımı çıkar.
Doğru sonuca hatalı yöntemle gelindiyse bunu açıkça belirt. Okunamayan el yazısını tahmin etme.
PDF içinde basılı bir cevap anahtarı varsa yerini ve bunun öğrenci işaretlerinden neden ayrı olduğunu answerKeyEvidence alanında belirt. Manuel cevap anahtarı verilmişse onu kullan. Güvenilir cevap anahtarı yoksa doğru/yanlış uydurma; ilgili soruları uncertain yap ve needsTeacherReview=true üret.
Belgede birden fazla test varsa hepsini belge kapsamında analiz et; program dışarıdan soru sayısı dayatmayacak. Soru kimliği yalnız basılı/orijinal soru numarasıdır.
Üst düzey öğrenci karnesini reasoningProfile içinde strengths, recurringErrors, conceptualGaps, proceduralGaps, attentionPatterns, recommendedActions ve summary alanlarıyla üret.
`}
