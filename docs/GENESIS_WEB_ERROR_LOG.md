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

## 11. Public student / online token route auth regresyonu
Tarih: 2026-09-23

Hata:
Public öğrenci portalı ve online sınav token URL'leri global auth middleware tarafından 401/403 ile engellenebiliyordu.

Kök neden:
Global GENESIS auth guard public token yollarını allowlist dışında bırakmıştı.

Çözüm:
Public öğrenci ve online sınav yolları, yönetici/kurum korumalarını gevşetmeden açıkça allowlist'e alındı:
- /coaching/student/
- /api/coaching/public/
- /online/
- /api/online/public/
- /api/online/session/
- /api/online/internet-test/

Deploy:
- cloudflare-release commit: e60e5fcb84981ddd8e2ccb238fdac56f9adbe0b6
- Fast Cloudflare Package Deploy run: 35841653319
- sonuç: SUCCESS

Doğrulama:
- main commit: e8f7ff1a13e8c2b7f8cf083459c23aa4807dc4a6
- Cloudflare GENESIS Inventory run: 35842053135
- invalid token public yolları 401/403 yerine beklenen 404 döndürdü.

## 12. Derin inventory workflow tanım hatası
Tarih: 2026-09-23

Hata:
Cloudflare GENESIS Inventory run 35847827110 workflow başlamadan failure oldu.

Kök neden:
Workflow içine eklenen karmaşık gömülü regex/Python audit bloğu YAML/script bütünlüğünü bozdu.

Production etkisi:
Yok. Bu yalnız read-only inventory workflow değişikliğiydi; deploy yapılmadı.

Çözüm:
Karmaşık contract analizini workflow içine gömmek yerine canlı source snapshot artifact'a çıkarıldı. Workflow yalnız güvenli source extraction + Python compileall + node --check yapacak şekilde sadeleştirildi.
- düzeltme commit: b22922386c9a0648fb645c409199b9ee84992d51
- inventory run: 35847904413
- sonuç: SUCCESS

## 13. Online internet-test unknown token yanlış STARTING davranışı
Tarih: 2026-09-23

Hata:
GET /api/online/internet-test/{public_token} için biçim olarak geçerli fakat sistemde bulunmayan token, public tunnel hazır değilse:
HTTP 200
{"ok":false,"status":"STARTING",...}
döndürebiliyordu.

Beklenen:
Bilinmeyen sınav tokenı HTTP 404 vermelidir.

Kök neden:
online_exam_module.py içindeki internet-test endpointi tokenın veritabanında varlığını doğrulamadan _tunnel_info / _tunnel_start akışına geçiyordu.

Çözüm:
Tunnel kontrolünden önce:
if not online_row_by_token(public_token):
    raise HTTPException(404,"Online sınav bulunamadı.")
kontrolü eklendi.

İzole doğrulama:
Disposable production-source testinde unknown token HTTP 404 + "Online sınav bulunamadı." verdi.

Production deploy:
- workflow fix commit: f53f7696698e74d0ed6c1caa59406832ef3883bc
- release trigger commit: 6ae24866667d71dfa077070b54c58c055362a8d7
- Fast Cloudflare Package Deploy run: 35848771978
- sonuç: SUCCESS
- Worker version: c37ee267-f427-4b8d-b00f-6aabd4062d4d
- Container version: 40

Post-deploy bağımsız doğrulama:
- main commit: ba4ffe7b89f134275b42c9b13674a5cffccf1d89
- inventory run: 35849074659
- /api/online/internet-test/genesis-audit-invalid-token => HTTP 404
- response: "Online sınav bulunamadı."
- container failed=0
- health.errors=[]
- observability logs enabled=true
- 23 kritik static asset HTTP 200
- 14 kritik JavaScript syntax check başarılı

## 14. Online-token hotfix release workflow YAML parse hataları
Tarih: 2026-09-23

İlk hata:
Fast Cloudflare Package Deploy run 35848675733 workflow parse aşamasında failure oldu.

Kök neden:
Dockerfile'a eklenecek heredoc gövdesinin YAML indentation'ı bozuktu.

İkinci hata:
Fast Cloudflare Package Deploy run 35848723254 yine workflow parse aşamasında failure oldu.

Kök neden:
Gömülü Python triple-quoted string kapanış satırları YAML kolon 0'a düşüyordu.

Production etkisi:
İki run da workflow başlamadan başarısız oldu; production'a deploy yapılmadı.

Çözüm:
Hotfix betiği YAML-safe tek satır string literal yapısına çevrildi.
- workflow commit: f53f7696698e74d0ed6c1caa59406832ef3883bc
- başarılı deploy run: 35848771978

## 15. 2026-09-23 tam denetim sonucu
Canlı production source snapshot GitHub Actions üzerinden alındı.

Doğrulamalar:
- uygulama: 0.15.2
- schema: 14
- storage: ok
- persistent storage: r2-fuse
- Worker version: c37ee267-f427-4b8d-b00f-6aabd4062d4d
- Worker version number: 53
- Container version: 40
- container failed instance: 0
- health errors: []
- observability logs: enabled
- tüm backend Python kaynakları compileall başarılı
- tüm aktif frontend JavaScript kaynakları node --check başarılı
- 23 kritik statik varlık HTTP 200
- 14 kritik JS HTTP/syntax audit başarılı

Disposable production-source entegrasyon testleri:
- 33 auth/curriculum/student/coaching senaryosu: 0 hata
- 19 topic/exam/source/crop/question senaryosu: 0 hata
- 16 online sınav uçtan uca senaryosu: 0 hata
- toplam 68 senaryo: 0 hata

Not:
Son auditte /api/auth/setup-status {"admin_configured":false} döndürmektedir. Mevcut uygulama ilk login ile admin oluşturmayı tasarım olarak desteklemektedir. Bu nedenle tek başına hata olarak sınıflandırılmadı ve production'da yapay kimlik bilgisi oluşturulmadı.

## 16. Çalışma protokolü — TinyFish
Tarih: 2026-09-23

Kullanıcının açık talimatı:
GENESIS WEB çalışmalarında TinyFish hiçbir koşulda kullanılmayacaktır.

Uygulama:
Bundan sonraki production envanter, kaynak analizi, deploy ve doğrulamalar GitHub / GitHub Actions / Cloudflare hattıyla yürütülmelidir.

## Kural
Yeni hatalar bu dosyaya tarih, adım, hata metni, kök neden ve çözüm ile eklenmelidir.
