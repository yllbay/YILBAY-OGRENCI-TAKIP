function homeworkMathVerificationInstruction(){return `LUNA MATEMATİK İKİNCİ GEÇİŞ PROTOKOLÜ:
Bu çağrıda yalnız verilen hedef soruları yeniden incele. PDF'nin diğer sorularını raporlama.
Her hedef için sectionKey, section, page ve printedNumber kimliğini aynen koru. Önce öğrencinin görünür el yazısındaki matematiksel ifadeleri SATIR SATIR transkribe et. +, -, ×, ÷, /, =, <, >, ≤, ≥, parantez, üs, kök, kesir çizgisi ve değişken sembollerini dikkatle ayır.
Okunamayan sembolü tahmin etme; transcriptionLines içinde [BELİRSİZ] yaz ve symbolConfidence değerini düşür.
Transkripsiyon tamamlanmadan matematiksel yorum yapma. Ardından satırlar arasındaki işlemleri yeniden hesapla ve finalStatus değerini correct|wrong|blank|uncertain olarak ver.
Yanlışsa firstErrorStep ilk gerçekten hatalı matematik adımı olmalı. errorCategory conceptual|arithmetic|attention|method|incomplete|uncertain değerlerinden biri olsun. betterApproach kısa ve matematiksel olarak doğru çözüm yolunu versin.
Sembol güveni 0.75 altındaysa finalStatus=uncertain yap; kesin hüküm verme.
Yalnız geçerli kısa JSON döndür.
`}
