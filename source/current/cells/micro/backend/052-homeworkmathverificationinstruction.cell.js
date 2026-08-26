function homeworkMathVerificationInstruction(){return `LUNA YÜKSEK ÇÖZÜNÜRLÜKLÜ MATEMATİK DOĞRULAMA PROTOKOLÜ:
Bu çağrıda yalnız verilen hedef soruları, kendilerine ait yüksek çözünürlüklü SAYFA GÖRÜNTÜLERİ üzerinde yeniden incele. PDF'nin tamamı bu çağrıda yoktur.
Her hedef için sectionKey, section, page ve printedNumber kimliğini aynen koru. Önce öğrencinin görünür el yazısındaki matematiksel ifadeleri SATIR SATIR transkribe et. +, -, ×, ÷, /, =, <, >, ≤, ≥, parantez, üs, kök, kesir çizgisi ve değişken sembollerini ayrı ayrı doğrula.
Okunamayan sembolü tahmin etme; transcriptionLines içinde [BELİRSİZ] yaz ve symbolConfidence değerini düşür.
Transkripsiyon tamamlanmadan matematiksel yorum yapma. Sonra işlemleri satır satır yeniden hesapla ve finalStatus değerini correct|wrong|blank|uncertain olarak ver.
Yanlışsa firstErrorStep ilk gerçekten hatalı matematik adımı olmalı. errorCategory conceptual|arithmetic|attention|method|incomplete|uncertain değerlerinden biri olsun. betterApproach kısa ve matematiksel olarak doğru çözüm yolunu versin.
Sembol güveni 0.80 altındaysa finalStatus=uncertain yap; kesin hüküm verme.
Yalnız geçerli kısa JSON döndür.
`}
