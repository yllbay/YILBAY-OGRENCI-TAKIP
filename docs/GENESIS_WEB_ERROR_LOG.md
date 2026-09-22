# GENESIS WEB — TARİHSEL HATA GÜNLÜĞÜ

> Yeni ChatGPT volume sohbetlerine aktarılacak doğrulanmış geliştirme/deploy hata geçmişi.

## 1. Eski production paket kaynağı eksik
Eski durum raporunda deployment_status:
BLOCKED_MISSING_CURRENT_CONTAINER_SOURCE
Sebep: current Dockerfile, Worker entrypoint, Wrangler container config ve kalıcı storage adapter kaynaklarının eksik olması.
Çözüm: canlı Cloudflare Worker/Versions/Containers envanteri salt-okunur olarak çıkarıldı.

## 2. Cloudflare token verify HTTP 400
Hata:
code 6003 — Invalid request headers
Sebep: ilk API token değerinin ekran görüntüsü/OCR üzerinden alınması veya yanlış karakter içermesi olasılığı.
Çözüm: Cloudflare'da yeni API Token doğrudan kopyalandı. /user/tokens/verify HTTP 200 oldu.

## 3. Worker listesi HTTP 403
Hata:
code 10000 — Authentication error
Sebep: token'da yalnız Containers → Edit vardı; Workers Scripts erişimi yoktu.
Çözüm:
Account → Workers Scripts → Edit eklendi.
Cloudflare inventory tüm adımları geçti.

## 4. İlk rollout doğrulaması yanlış health varsayımı
İlk deploy Cloudflare'a gerçekten başarılı biçimde çıktı ancak workflow active instance >= 1 beklediği için başarısız işaretlendi.
Cloudflare container scale-to-zero davranışı nedeniyle active instance 0 olabilir.
Çözüm: rollout kontrolü version advance + failed=0 + health.errors=0 üzerinden düzeltildi.

## 5. İlk deploy observability ayarını kapattı
Wrangler deploy farkında container observability.logs.enabled true → false değişikliği görüldü.
Çözüm: release config mevcut log semantiğini koruyacak biçimde düzeltildi ve son production doğrulamasında logs.enabled=true teyit edildi.

## 6. Base64 tar bundle CRC hatası
Hata:
gzip: stdin: invalid compressed data -- crc error
tar: Child returned status 1
Sebep: tek büyük base64 bundle aktarımı bozuldu.
Çözüm: XZ sıkıştırılmış iki parçalı release bundle akışı oluşturuldu.

## 7. Worker wrapper multipart parse hatası
Wrangler dry-run:
index.js:2:6 Syntax error
Dosyada multipart boundary satırı index.js içine girmişti.
Sebep: content/v2 yanıtından ilk multipart payload'un yanlış seçilmesi.
Çözüm: GenesisContainer + GENESIS_CONTAINER + container.fetch imzalarını taşıyan tek modül seçilecek biçimde parser düzeltildi.

## 8. Smoke test 401/403 beklenti hatası
Production API gerçek davranışı:
HTTP 403
{"detail":"Koçluk alanı için GENESIS oturumu gerekli."}
Workflow yanlışlıkla HTTP 401 ve AUTH_REQUIRED kodu bekliyordu.
Çözüm: smoke testi mevcut GENESIS auth davranışı olan 403 + gerçek mesaj ile hizalandı.

## 9. Concurrency sırasında önceki run iptali
Yeni release tetikleyicisi aynı concurrency grubundaki önceki run rollout kontrolündeyken geldi.
Önceki run'ın deploy adımı başarılıydı ancak kontrol adımı cancelled oldu.
Çözüm: son doğrulama ayrı hafif production smoke workflow'u ile gerçekleştirildi.

## 10. Son durum
GENESIS Production Smoke sonucu SUCCESS.
Root, curriculum auth guard, curriculum UI, container health ve observability doğrulandı.

## Kural
Yeni hatalar bu dosyaya tarih, adım, hata metni, kök neden ve çözüm ile eklenmelidir.
