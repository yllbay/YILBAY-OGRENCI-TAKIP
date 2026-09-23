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

## 17. Tek ADMIN / şifresiz doğrudan giriş modu
Tarih: 2026-09-23

Kullanıcı talimatı:
GENESIS yalnız ADMIN olarak çalışacak; kullanıcı adı/şifre sorulmayacak; diğer kullanıcılar kaldırılacak.

Uygulama değişikliği:
- Oturum yoksa backend otomatik ADMIN session oluşturur.
- /api/auth/me otomatik ADMIN kimliğini doğrular.
- institutions kayıtları temizlenir.
- INSTITUTION auth session kayıtları temizlenir.
- Kurum veri klasörleri ve içerikleri silinmez.
- Yeni kurum kaydı ve kurum kullanıcı yönetimi API işlemleri HTTP 410 ile kapatılmıştır.
- İlgili kurum oluşturma/yönetme ve admin şifre değiştirme UI kontrolleri kaldırılmıştır.
- Public öğrenci ve online sınav token yolları bu otomatik ADMIN davranışının dışında tutulmuştur.

Production deploy:
- Fast Cloudflare Package Deploy run: 35852251918
- sonuç: SUCCESS
- Container version: 43

Post-deploy smoke:
- /api/auth/me => authenticated=true, role=ADMIN, institution_id=null, must_change_password=false
- /api/coaching/curriculum/tree => HTTP 200
- /api/admin/institutions => []
- POST /api/admin/institutions => HTTP 410
- root ve curriculum UI => HTTP 200
- invalid online token => HTTP 404 davranışı korunuyor

Not:
Bu bir hata düzeltmesinden çok kullanıcı tarafından talep edilen auth mimarisi değişikliğidir. Güvenlik sonucu olarak production URL'sine erişebilen herkes ADMIN yetkisine sahip olur.

## 18. Koçluk Stüdyosu yan panel hızlı işlemleri
Tarih: 2026-09-23

Talep:
Koçluk Stüdyosu yan paneline "Öğrenci Ekle" ve "Ders Ekle" düğmelerinin eklenmesi.

Başlangıç durumu:
- Yan panelde öğrenci ekleme için yalnız küçük "+" ikon düğmesi vardı.
- Ders ekleme/atama işlemi yalnız seçili öğrencinin Dersler sekmesindeki mevcut akıştan yapılabiliyordu.

Uygulama:
- Mevcut `studentForm()` ve `courseForm()` akışları yeniden kullanıldı.
- Yeni backend endpointi, schema veya storage değişikliği yapılmadı.
- "Ders Ekle" için seçili öğrenci guard'ı eklendi.
- Patch `cloudflare/coaching_sidebar_actions.py` ile idempotent olarak uygulanır.
- HTML / JS / CSS üzerinde `GENESIS_COACHING_SIDEBAR_ACTIONS` marker'ı kullanılır.

Doğrulama:
- production-source snapshot üzerinde lokal patch testi: SUCCESS
- patched `coaching-v2.js`: node --check SUCCESS
- Fast Cloudflare Package Deploy run 35857303418: SUCCESS
- post-deploy Cloudflare GENESIS Inventory run 35857665059: SUCCESS
- canlı snapshot'ta "+ Öğrenci Ekle" ve "+ Ders Ekle": doğrulandı
- 23 kritik statik asset: HTTP 200
- 14 kritik JavaScript syntax kontrolü: başarılı
- container failed instance: 0
- health errors: []
- observability logs: enabled
- Worker version ID: 127aa738-4b0b-4db5-bb19-4b5209eeb748
- Worker version number: 57
- Container version: 44

Production etkisi:
İstenen UI geliştirmesi dışında doğrulanmış regresyon veya yeni hata gözlenmedi. Mevcut single-ADMIN auth, curriculum ve invalid-token davranışları korunmuştur.

## 19. Koçluk Ders Ekle hızlı davranışının bağımsız çalışma alanına geçirilmesi
Tarih: 2026-09-23

Durum:
İlk yan panel geliştirmesinde "Ders Ekle" düğmesi mevcut seçili öğrencinin Dersler sekmesine geçip `courseForm()` akışını açıyordu. Bu ilk talebi karşılıyordu; ancak kullanıcı daha sonra kapsamı açıkça ayrıntılandırarak bu davranışın istenmediğini belirtti.

Yeni gereksinim:
- "ÖĞRENCİLER" başlığı kaldırılacak.
- Arama alanı en üstte olacak.
- Altında Öğrenci Ekle, ardından Ders Ekle bulunacak.
- Ders Ekle ana sayfadaki Konular / Konu Soruları / Testler menülerinin bağımsız bir kopyasını açacak.
- Bu kopyaya ileride farklı işlevler yüklenirken ana sayfa etkilenmeyecek.

Risk:
Canlı container image üzerinde önceki `GENESIS_COACHING_SIDEBAR_ACTIONS` patch'i zaten bulunduğu için yalnız orijinal HTML/JS yapısını bekleyen yeni bir patch deploy sırasında başarısız olabilirdi. Ayrıca eski deploy step'i bırakılırsa sonraki release'lerde yeni sidebar yapısını yeniden eski quick-action formatına çevirmeye çalışabilirdi.

Çözüm:
- Yeni migration-aware patch `cloudflare/coaching_sidebar_coursecopy.py` oluşturuldu.
- Patch hem orijinal sidebar'ı hem production'daki eski quick-action varyantını tanıyacak şekilde tasarlandı.
- Eski `Apply coaching sidebar quick actions` deploy adımı kaldırıldı.
- Eski `sideAddCourse` handler'ı production JS'ten çıkarıldı.
- Yeni bağımsız `courseCopy` state'i ve `course-copy-*` DOM/CSS isim alanı eklendi.
- Kopya yalnız `GET /api/topics`, `GET /api/test-tree` ve `GET /api/questions?topic_id=...` çağrılarını kullanır; ana sayfa state'ine veya mutasyon işlevlerine bağlanmaz.
- Eski `cloudflare/coaching_sidebar_actions.py` release branch'ten emekliye ayrıldı.

Doğrulama:
- orijinal production-source üzerinde lokal migration testi: SUCCESS
- önceki quick-action varyantı simülasyonu üzerinde migration testi: SUCCESS
- idempotency kontrolü: SUCCESS
- patched `coaching-v2.js` node --check: SUCCESS
- Fast Cloudflare Package Deploy run 35859953479: SUCCESS
- Worker version ID: c8d8c872-4570-446e-9506-e9d00bd8c302
- Worker version number: 58
- Container version: 45
- Cloudflare GENESIS Inventory run 35860433564: SUCCESS
- 23 kritik statik asset: HTTP 200
- 14 kritik JavaScript syntax kontrolü: başarılı
- canlı HTML'de "ÖĞRENCİLER" başlığı yok
- canlı sidebar sırası: arama → Öğrenci Ekle → Ders Ekle → öğrenci listesi
- canlı JS'te eski `sideAddCourse` handler yok
- container failed instance: 0
- health errors: []
- observability logs: enabled

Production etkisi:
Önceki hızlı "Ders Ekle → courseForm()" davranışı kullanıcı talebi doğrultusunda kaldırıldı ve bağımsız kopya mimarisiyle değiştirildi. Backend, schema, storage, single-ADMIN auth, curriculum ve public invalid-token davranışlarında değişiklik yapılmadı.

## 20. Koçluk Stüdyosu değişikliğinin tarayıcıda görünmemesi — immutable cache
Tarih: 2026-09-23

Hata:
Koçluk Stüdyosu sidebar ve bağımsız Ders Ekle alanı production container image'ında mevcut ve deploy/inventory kontrolleri başarılı olmasına rağmen kullanıcı tarayıcıda hiçbir değişiklik görmedi.

Kök neden:
`coaching-v2.html`, `coaching-v2.js` ve `coaching-v2.css` çağrılarında eski `?v=0.15.1` query değeri korunmuştu.
Backend cache middleware'i query parametresi bulunan `/static/*` varlıklarını:
`Cache-Control: public, max-age=31536000, immutable`
olarak işaretliyordu.
Bu nedenle tarayıcı daha önce indirdiği eski Koçluk JS/CSS dosyalarını yeniden istemeden kullanabiliyordu.

Neden önceki doğrulama kaçırdı:
- production container kaynakları doğruydu
- static assetler HTTP 200 dönüyordu
- JS syntax testleri geçiyordu
- fakat smoke test response cache header'ını ve asset version invalidation'ını kontrol etmiyordu

Çözüm:
- `cloudflare/coaching_cache_policy.py` eklendi.
- `coaching-v2.js/css` query sürümü `0.15.2-coaching-2` olarak değiştirildi.
- `/static/coaching-v2.js` ve `/static/coaching-v2.css` için query parametresinden bağımsız `no-store, no-cache, must-revalidate` cache policy uygulandı.
- Release smoke testine canlı response header doğrulaması eklendi.
- Koçluk JS/CSS response'larında `Cache-Control: no-store` bulunmadığında deploy artık başarısız sayılacaktır.

Production:
- Fast Cloudflare Package Deploy run: 35861430658
- sonuç: SUCCESS
- Worker version ID: 38d23959-2051-4fab-91df-ab7edc14eb61
- Worker version number: 59
- Container version: 46
- Container image: registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:3512f2bc64094a76ac08c01ecf3209750ad7ee7cc54f511ed1062ab3c5b97a0b

Bağımsız doğrulama:
- Cloudflare GENESIS Inventory run: 35861901562
- sonuç: SUCCESS
- canlı app.py içinde `GENESIS_COACHING_HOT_ASSET_CACHE_V1` mevcut
- canlı coaching-v2.html yeni JS/CSS query sürümlerini içeriyor
- 23 kritik statik asset HTTP 200
- 14 JavaScript syntax kontrolü başarılı
- container failed=0
- health.errors=[]
- observability logs enabled

Production etkisi:
Koçluk Stüdyosu değişikliklerinin tarayıcıda eski immutable assetler nedeniyle gizlenmesi engellendi. Diğer versioned statik assetlerin mevcut cache politikası değiştirilmedi.

## 21. Açılış dashboard release prebuild — Docker max depth exceeded
Tarih: 2026-09-23

Hata:
GENESIS açılış Yönetim Paneli release denemesinde Fast Cloudflare Package Deploy run `35871205798`, `Prebuild patched container safely` adımında başarısız oldu.

Hata metni:
`failed to prepare ...: max depth exceeded`

Hatanın görüldüğü Dockerfile adımı:
`COPY coaching_sidebar_coursecopy.py /tmp/coaching_sidebar_coursecopy.py`

Kök neden:
- Production release hattı canlı, zaten çok katmanlı container image'ını base image olarak kullanıyordu.
- Biriken production hotfix/patch dosyalarının her biri Dockerfile'a ayrı `COPY` ve `RUN` katmanları ekliyordu.
- Yeni dashboard patch'i eklendiğinde BuildKit'in izin verdiği image/layer derinliği prebuild sırasında aşıldı.
- Hata dashboard JavaScript/CSS sözdiziminden kaynaklanmadı; package validation aşaması başarılıydı.

Production etkisi:
Yok. İlk run'da `Deploy one tested package` adımı çalışmadı ve production mevcut Worker v59 / Container v46 üzerinde kaldı.

Çözüm:
- Online token, single-admin, coaching sidebar, coaching cache ve opening dashboard production patch'leri ayrı Docker katmanları oluşturmak yerine tek toplu `COPY` + tek toplu `RUN` katmanında birleştirildi.
- release workflow fix commit: `4414e0f62cba5f43e40e092489c8aefc3b63dc76`
- retry trigger commit: `741f7554de9943745511166740c59917aee40028`
- Fast Cloudflare Package Deploy run: `35871495303`
- sonuç: SUCCESS
- Worker: `26942052-2d03-4e6c-a531-cd94892d8c4b` / version number 60
- Container version: 47
- Container image: `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:2a4af72ce7b67c646777324bae1126686a59907c97ace04ff6c4bb4bb8a999fd`

Bağımsız doğrulama:
- main inventory verification commit: `475a8efdb8216e3a6654a54407b22abf2a77690c`
- Cloudflare GENESIS Inventory run: `35872114484`
- sonuç: SUCCESS
- yeni açılış dashboard kaynak marker'ları production image içinde doğrulandı
- root HTTP 200
- 24 kritik statik asset HTTP 200
- 14 kritik JavaScript syntax kontrolü başarılı
- container failed=0
- health.errors=[]
- observability logs enabled

## Kural
Yeni hatalar bu dosyaya tarih, adım, hata metni, kök neden ve çözüm ile eklenmelidir.
