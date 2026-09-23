# GENESIS WEB — GÜNCEL GELİŞTİRME DEVİR DOSYASI

> Bu dosya yeni ChatGPT geliştirme sohbetlerinin başlangıç bağlamıdır.
> Her önemli web geliştirme/deploy aşamasından sonra güncellenmelidir.

## Protokol
- Geliştirme adım adım yürütülür.
- Bir adım kullanıcı tarafından onaylanmadan sonraki adıma geçilmez.
- TinyFish GENESIS WEB çalışmalarında KESİNLİKLE kullanılmaz. Kullanıcının 2026-09-23 tarihli açık talimatıdır.
- GitHub mümkün olduğunca paket/deploy köprüsü olarak kullanılır.
- Production yapısı tahmin edilmez; önce canlı yapı doğrulanır.
- Yerel GENESIS ile web GENESIS birbirinden ayrıdır; kullanıcı açıkça istemedikçe yerelden web'e aktarım yapılmaz.

## Proje
- GitHub: yllbay/YILBAY-OGRENCI-TAKIP
- Production Worker: genesis-web-0152
- Production URL: https://genesis-web-0152.yilbayonurcelik.workers.dev/
- Uygulama sürümü: 0.15.2
- source/current paket sürümü: 0.9.0

## Doğrulanmış Cloudflare mimarisi
- Worker entrypoint: index.js
- Container class: GenesisContainer
- Durable Object binding: GENESIS_CONTAINER
- R2 binding: GENESIS_DATA
- R2 bucket: genesis-web-0152-data
- Container application ID: a03b84d1-3560-43de-8d60-55bbca682961
- Container runtime: Firecracker
- Instance type: standard-1
- Kaynaklar: 0.5 vCPU / 4 GiB RAM / 8 GB disk
- Ağ: private
- Deploy aracı: Wrangler
- Container observability logs: enabled
- Kalıcılık: mevcut GENESIS DATA/SQLite yapısı korunur.
- Son doğrulanmış Worker version ID: 333099cd-a686-4d97-8e31-df00ea4f0ebb
- Son doğrulanmış Worker version number: 81
- Son doğrulanmış container version: 61
- Son doğrulanmış container image: registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:0e607006eb87456b2305bd6e10df6141e7e805129880d103107e888e3649c82e

## GitHub dalları
- main: production envanter/smoke altyapısı ve kaynak
- web-step1-curriculum: Adım 1 Node geliştirme dalı
- cloudflare-release: paketlenmiş Cloudflare release hattı

## Web geliştirme süreci — baştan bugüne

### 1. Canlı sistemin ilk analizi
Production Worker dışarıdan incelendi. Ana sayfada GENESIS giriş ekranı görüldü. Uygulama içi kaynak ile canlı Cloudflare container yapısı başlangıçta tam eşleştirilemedi; eski raporda current container source eksik olduğu için deploy engelliydi.

### 2. Adım 1 tanımı
Kullanıcı Adım 1 kapsamını şu şekilde belirledi:
Ders → Ünite → Alt Başlık hiyerarşisinin koçluk modülüne merkezi olarak yüklenmesi ve yönetilmesi.

Kapsam:
- ders ekleme/düzenleme/pasifleştirme/sıralama
- ünite ekleme/düzenleme/pasifleştirme/sıralama
- alt başlık ekleme/düzenleme/pasifleştirme/sıralama
- CSV toplu içe aktarma
- tekrar kayıt koruması/idempotency
- fiziksel silme yok
- öğrenci atama/haftalık plan/AI önerisi bu adımın dışında

### 3. İlk uygulama geliştirmesi
web-step1-curriculum dalında:
- source/current/app/curriculum-store.js
- source/current/app/curriculum-store.test.js
- source/current/app/public/curriculum-step1.js
- server.js API route entegrasyonu
- index.html script entegrasyonu
oluşturuldu.
İlk CI testleri geçti.

### 4. Cloudflare erişim köprüsü
GitHub Actions üzerinden Cloudflare read-only inventory workflow'u kuruldu.
GitHub Secrets:
- CLOUDFLARE_API_TOKEN
- CLOUDFLARE_ACCOUNT_ID

İlk token OCR/kopyalama kaynaklı hatalıydı; yenisi ile token verify başarılı oldu.
Token'a Containers Edit yanında Workers Scripts Edit yetkisi eklendi.

### 5. Canlı Cloudflare yapısının keşfi
Worker Versions/Containers envanteriyle canlı yapının klasik Worker değil Container Worker olduğu doğrulandı.
GenesisContainer, GENESIS_CONTAINER ve GENESIS_DATA binding'leri doğrulandı.
Aktif container application, image registry ve rollout davranışı keşfedildi.

### 6. Güvenli release hattı
cloudflare-release dalında:
- Fast Cloudflare Package Deploy
- canlı Worker wrapper'ını deploy anında hydrate etme
- canlı container image'ını base olarak kullanma
- dry-run
- Docker prebuild
- container iç dosya doğrulaması
- Wrangler deploy
- rollout kontrolü
- production smoke test
akışı kuruldu.

### 7. Adım 1 production adaptasyonu
Canlı container'ın backend'i Node değil Python/FastAPI tabanlı olduğundan Adım 1 production paketi canlı backend yapısına adapte edildi.
Doğrulanan production bileşenleri:
- /api/coaching/curriculum/tree
- /api/coaching/curriculum/action
- ADMIN / INSTITUTION erişim kontrolü
- coaching-curriculum frontend dosyaları
- mevcut GENESIS SQLite DATA alanında kalıcılık

### 8. Production deploy
Adım 1 container image'ı Cloudflare Registry'ye gönderildi ve Worker/Container rollout gerçekleştirildi.
Son doğrulanmış Worker version ID:
6607a54e-eb67-492c-8401-1a9ada9c8547
Container rollout version:
37

### 9. Son production smoke sonucu
GENESIS Production Smoke başarıyla tamamlandı:
- root HTTP 200
- GENESIS ana uygulaması erişilebilir
- /api/coaching/curriculum/tree yetkisiz erişimde HTTP 403
- mesaj: "Koçluk alanı için GENESIS oturumu gerekli."
- coaching curriculum statik UI HTTP 200
- Ders / Ünite / Alt Başlık UI doğrulandı
- container failed instance = 0
- health errors = 0
- observability logs = enabled

## 10. 2026-09-23 tam production denetimi ve düzeltmeler

Kullanıcının talebiyle GENESIS production üzerinde geniş kapsamlı kontrol uygulandı. Kullanıcının açık talimatı gereği TinyFish bundan sonra hiçbir koşulda kullanılmayacaktır; denetim ve deploy hattı GitHub / GitHub Actions / Cloudflare üzerinden yürütülür.

### Güncel production gerçekliği
Eski handoff sürümü 0.11.2 iken canlı health endpointinin ve canlı container kaynaklarının daha ileri olduğu doğrulandı:
- uygulama sürümü: 0.15.2
- schema: 14
- storage: ok
- persistent storage: r2-fuse
- runtime: container
- Drive storage: service_account ve root folder configured
- Worker: c37ee267-f427-4b8d-b00f-6aabd4062d4d, version number 53
- Container rollout: version 40
- container failed instance: 0
- container health errors: []
- observability.logs.enabled: true

### Public token route regresyonu
Tam HTTP audit sırasında öğrenci ve online sınav public token yollarının global auth middleware tarafından yanlışlıkla engellendiği önceki regresyon doğrulandı ve public route allowlist düzeltmesi production'a alındı.
Doğrulanan invalid-token davranışları:
- /coaching/student/<invalid-token>: 404
- /api/coaching/public/<invalid-token>/*: 404
- /online/<invalid-token>: 404
- /api/online/public/<invalid-token>/*: 404
- /api/online/session/<invalid-token>: 404

Public route düzeltme deploy'u:
- cloudflare-release commit: e60e5fcb84981ddd8e2ccb238fdac56f9adbe0b6
- deploy run: 35841653319
- sonuç: SUCCESS

### Online internet-test invalid token hatası
Ek denetimde /api/online/internet-test/{public_token} endpointinde gerçek bir mantık hatası bulundu.
Eski davranış:
- biçim olarak geçerli ama sistemde olmayan token, tünel hazır değilse HTTP 200 + STARTING dönebiliyordu.
Kök neden:
- endpoint tokenın veritabanında varlığını kontrol etmeden tunnel state kontrolüne geçiyordu.
Çözüm:
- online_row_by_token(public_token) doğrulaması tunnel kontrolünden önce eklendi.
- bilinmeyen token artık HTTP 404 ve "Online sınav bulunamadı." döndürüyor.

Production düzeltme:
- cloudflare-release workflow fix commit: f53f7696698e74d0ed6c1caa59406832ef3883bc
- release trigger commit: 6ae24866667d71dfa077070b54c58c055362a8d7
- Fast Cloudflare Package Deploy run: 35848771978
- sonuç: SUCCESS
- Worker version: c37ee267-f427-4b8d-b00f-6aabd4062d4d
- Container version: 40
- post-deploy smoke: SUCCESS

Bağımsız post-deploy inventory:
- main commit: ba4ffe7b89f134275b42c9b13674a5cffccf1d89
- Cloudflare GENESIS Inventory run: 35849074659
- sonuç: SUCCESS
- /api/online/internet-test/genesis-audit-invalid-token: HTTP 404
- 23 kritik statik asset: tamamı HTTP 200
- 14 kritik JavaScript dosyası: tamamı node --check başarılı

### Derin canlı kaynak denetimi
GitHub Actions inventory genişletildi ve canlı container image içindeki production kaynaklarının tam audit snapshot'ı alındı.
- main commit: b22922386c9a0648fb645c409199b9ee84992d51
- inventory run: 35847904413
- sonuç: SUCCESS
- tüm backend Python kaynakları compileall ile başarılı
- tüm aktif frontend JavaScript kaynakları node --check ile başarılı
- backend route envanteri çıkarıldı
- frontend API çağrıları backend route'larıyla çapraz kontrol edildi
- localhost:8765 web-capture çağrılarının yerel snapshot companion'a ait olduğu doğrulandı; web backend'e taşınmadı.

### Disposable production-source entegrasyon testleri
Canlı production source snapshot'ı izole, boş SQLite ortamında çalıştırıldı. Production verisine yazılmadı.
- auth / first setup / curriculum / student portal / coaching / goals / learning / insights / desk: 33 senaryo, 0 hata
- topic tree / class / exam builder / PNG source / crop / question flows: 19 senaryo, 0 hata
- soru → sınav → PDF → online publish → öğrenci oturumu → cevap → submit → sonuç → close: 16 senaryo, 0 hata
- toplam: 68 senaryo, 0 hata

### Production auth durumu
Son audit sırasında /api/auth/setup-status:
{"admin_configured":false}
Bu, mevcut kodda first-login setup akışının desteklediği bir durumdur; tek başına hata sayılmaz. Kullanıcı tarafından gerçek production yönetici kimlik bilgisi verilmediği için production üzerinde yapay admin hesabı oluşturulmadı. Authenticated browser davranışları disposable production-source entegrasyon testleriyle doğrulandı.


## 11. 2026-09-23 tek ADMIN / şifresiz doğrudan giriş modu

Kullanıcının açık talimatı:
- GENESIS açılışında kullanıcı adı/şifre sorulmayacak.
- Uygulama doğrudan ADMIN yetkisiyle açılacak.
- Diğer kurum/kullanıcı hesapları kaldırılacak.
- Yeni kurum kullanıcısı oluşturma ve kurum kullanıcı yönetimi kapatılacak.

Uygulanan production davranışı:
- Auth middleware oturum yoksa otomatik ADMIN session üretir.
- /api/auth/me ilk istekte authenticated=true, role=ADMIN, institution_id=null, must_change_password=false döndürür.
- Kurum kullanıcı hesapları institutions tablosundan temizlenir.
- INSTITUTION rolündeki auth_sessions kayıtları temizlenir.
- Kurumlara ait veri klasörleri silinmez; yalnız hesap/oturum katmanı kaldırılır.
- /api/auth/register-institution kapalıdır.
- /api/admin/institutions GET dışındaki kurum yönetim işlemleri kapalıdır.
- Ana uygulamadaki "Yeni Kurum Oluştur", "Kurumları Yönet", "Yönetici Şifresini Değiştir" vb. kullanıcı yönetimi UI öğeleri kaldırılmıştır.
- Public öğrenci/online token yolları mevcut public davranışını korur; otomatik ADMIN session bu public token yollarına zorla uygulanmaz.

Release:
- cloudflare-release release trigger: single-admin-auto-session-v2
- Fast Cloudflare Package Deploy run: 35852251918
- sonuç: SUCCESS
- Container rollout: version 43
- production smoke: SUCCESS

Smoke doğrulamaları:
- root HTTP 200
- /api/auth/me: ADMIN otomatik oturum doğrulandı
- /api/coaching/curriculum/tree: HTTP 200, ADMIN erişimi doğrulandı
- /api/admin/institutions: HTTP 200 ve []
- yeni kurum kullanıcısı oluşturma denemesi: HTTP 410
- curriculum UI HTTP 200
- invalid online token davranışı 404 olarak korunuyor

Bu mod artık GENESIS WEB production için kanonik auth davranışıdır.

## 12. 2026-09-23 Koçluk Stüdyosu yan panel hızlı işlemleri

Kullanıcının açık talebi:
- Koçluk Stüdyosu yan paneline "Öğrenci Ekle" düğmesi eklenecek.
- Koçluk Stüdyosu yan paneline "Ders Ekle" düğmesi eklenecek.

Uygulama öncesi canlı production source snapshot incelendi. Mevcut koçluk akışında:
- öğrenci ekleme için mevcut `studentForm()` akışı,
- seçili öğrenciye ders atama için mevcut `courseForm()` akışı
zaten bulunuyordu. Yeni backend, schema veya veri modeli oluşturulmadı.

Uygulanan frontend davranışı:
- Yan panelde "+ Öğrenci Ekle" düğmesi mevcut öğrenci ekleme formunu açar.
- Yan panelde "+ Ders Ekle" düğmesi seçili öğrencinin Dersler sekmesine geçer ve mevcut ders ekleme/atama formunu açar.
- Öğrenci seçilmeden "Ders Ekle" tıklanırsa kullanıcıdan önce öğrenci seçmesi istenir.
- HTML / JS / CSS patch'i idempotent marker olarak `GENESIS_COACHING_SIDEBAR_ACTIONS` kullanır.
- Production patch dosyası: `cloudflare/coaching_sidebar_actions.py`.

Release kayıtları:
- patch dosyası commit: 192f6befa8887984a9f8939283d7322cf415c1e0
- release workflow commit: ed1b7b598f2d978f20fbe881dc8e2653d92415d7
- deploy trigger commit: 816e5a34e70674fd769c2e3bd31d1f4c6ed7a814
- Fast Cloudflare Package Deploy run: 35857303418
- sonuç: SUCCESS
- Worker version ID: 127aa738-4b0b-4db5-bb19-4b5209eeb748
- Worker version number: 57
- Container version: 44
- Container image: registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:36c3c6a752049d7672a768c520718defe0ea51b2617dabe5f8bc0967176a9fc6

Bağımsız post-deploy doğrulama:
- main inventory trigger commit: 9c9c824f4fa9f0ba7a177ca2c7451aa374c75b72
- Cloudflare GENESIS Inventory run: 35857665059
- sonuç: SUCCESS
- canlı `coaching-v2.html` içinde "+ Öğrenci Ekle" ve "+ Ders Ekle" doğrulandı
- `coaching-v2.js` syntax check başarılı
- ilgili HTML / JS / CSS statik assetleri HTTP 200
- toplam kritik statik asset kontrolü: 23/23 HTTP 200
- kritik JavaScript syntax kontrolü: 14/14 başarılı
- container failed instance: 0
- health errors: []
- observability logs: enabled
- canlı health: 0.15.2 / schema 14 / storage ok / r2-fuse
- public invalid-token 404 davranışları korunuyor

Bu değişiklik Adım 2 olarak sınıflandırılmamıştır; Adım 1 sonrası kullanıcı tarafından açıkça istenen sınırlı bir Koçluk Stüdyosu UI geliştirmesidir.

## 13. 2026-09-23 Koçluk Stüdyosu bağımsız Ders Ekle çalışma alanı

Kullanıcının önceki hızlı işlem talebini ayrıntılandıran yeni açık talebi:
- Sol paneldeki "ÖĞRENCİLER" başlığı kaldırılacak.
- Öğrenci arama alanı panelin en üstünde olacak.
- Aramanın altında sırasıyla "Öğrenci Ekle" ve "Ders Ekle" düğmeleri olacak.
- "Ders Ekle" seçili öğrenciye doğrudan ders atama formunu açmayacak.
- "Ders Ekle", ana GENESIS ekranındaki Konular / Konu Soruları / Testler menülerinin Koçluk Stüdyosu içinde bağımsız bir kopyasını açacak.
- Bu kopya ileride farklı işlevlerle geliştirilecek ve ana GENESIS sayfasının state, DOM veya işlevlerini etkilemeyecek.

Uygulanan mimari:
- Önceki geçici `sideAddCourse -> setTab('courses'); courseForm()` davranışı kaldırıldı.
- Yeni production patch: `cloudflare/coaching_sidebar_coursecopy.py`.
- HTML marker: `GENESIS_COACHING_SIDEBAR_COURSE_COPY_V1`.
- JS/CSS marker: `GENESIS_COACHING_COURSE_COPY_V1`.
- Sidebar sırası canlı kaynakta doğrulandı:
  1. `studentSearch`
  2. `addStudent`
  3. `addCourseWorkspace`
  4. `studentList`
- "ÖĞRENCİLER" başlığı production HTML'den kaldırıldı.
- Ders Ekle alanı için ayrı `courseCopy` state'i oluşturuldu.
- Ana sayfanın `app-0.10.7.js` state'i veya render fonksiyonları Koçluk Stüdyosu kopyasında kullanılmaz.
- Bağımsız kopya yalnız salt-okunur veri çağrıları yapar:
  - `GET /api/topics`
  - `GET /api/test-tree`
  - `GET /api/questions?topic_id=...`
- Kopyanın DOM/CSS isim alanı `course-copy-*` olarak ayrıdır.
- Öğrenci seçildiğinde bağımsız Ders Ekle çalışma alanı kapanır ve standart öğrenci dashboard'una dönülür.
- Backend endpoint, schema veya storage değişikliği yapılmadı.

Migration güvenliği:
- Yeni patch hem orijinal sidebar yapısını hem de daha önce production'a çıkmış `GENESIS_COACHING_SIDEBAR_ACTIONS` hızlı işlem varyantını tanıyıp dönüştürebilecek şekilde hazırlandı.
- Eski `cloudflare/coaching_sidebar_actions.py` deploy workflow'dan çıkarıldı ve release branch'ten emekliye ayrıldı.
- Patch idempotency ve iki başlangıç varyantı üzerinde lokal olarak doğrulandı.
- Patched `coaching-v2.js` için `node --check` başarılı.

Release kayıtları:
- ilk bağımsız patch commit: 862922530960e2599eb929f5da9b22d3dfce0061
- migration uyumluluk düzeltmesi: da45c8bc49a1afad9f9278c66092b544dbe9b022
- release workflow commit: d2a958f2ff268c27b44c9a9733a51903bb3e40de
- deploy trigger commit: 41691c0a18ba3a56dd73c71fee32b88a56711feb
- Fast Cloudflare Package Deploy run: 35859953479
- sonuç: SUCCESS
- Worker version ID: c8d8c872-4570-446e-9506-e9d00bd8c302
- Worker version number: 58
- Container version: 45
- Container image: registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:fbb8d87d7e967414cbb5788152cdfe28b39a83cfb40160a0cdbd2dc3d68fe39a
- eski hızlı patch cleanup commit: 87d63d55e46f1e3f57eae58aa396d96b51117a93

Bağımsız post-deploy inventory:
- main inventory trigger commit: 38b7ccd8f31be2c694cb12d008992a8c970cab29
- Cloudflare GENESIS Inventory run: 35860433564
- sonuç: SUCCESS
- canlı health: 0.15.2 / schema 14 / storage ok / r2-fuse
- 23 kritik statik asset: HTTP 200
- 14 JavaScript syntax kontrolü: başarılı
- `coaching-v2.html`: yeni sidebar marker mevcut, eski "ÖĞRENCİLER" başlığı yok
- `coaching-v2.js`: yeni bağımsız state marker mevcut, eski `sideAddCourse` handler yok
- `coaching-v2.css`: bağımsız `course-copy-*` stilleri mevcut
- container failed instance: 0
- health errors: []
- observability logs: enabled

Bu geliştirme de Adım 2 olarak sınıflandırılmamıştır; kullanıcı tarafından açıkça istenen Koçluk Stüdyosu UI/mimari düzenlemesidir.

## 14. 2026-09-23 Koçluk Stüdyosu görünmüyor — browser cache invalidation düzeltmesi

Kullanıcı bildirimi:
- Bağımsız Ders Ekle çalışma alanı production deploy ve inventory kontrollerinden geçmesine rağmen kullanıcı Koçluk Stüdyosu ekranında hiçbir değişiklik görmedi.

Canlı teşhis:
- Production container source snapshot'ında `/coaching` route'unun gerçekten `coaching-v2.html` döndürdüğü doğrulandı.
- Canlı `coaching-v2.html` yeni sidebar yapısını içeriyordu.
- Kök neden yanlış route değildi.
- `coaching-v2.html`, CSS ve JS'i hâlâ `?v=0.15.1` query değeriyle çağırıyordu.
- Backend cache middleware'i query parametresi olan tüm `/static/*` dosyalarını `public, max-age=31536000, immutable` olarak işaretliyordu.
- Böylece kullanıcı tarayıcısı eski `coaching-v2.js/css` dosyalarını bir yıl geçerli immutable cache'ten kullanabiliyordu.
- Önceki smoke test yalnız asset HTTP 200 ve içerik marker'larını kontrol ettiği için gerçek browser cache invalidation sorunu yakalanmamıştı.

Çözüm:
- Yeni production patch: `cloudflare/coaching_cache_policy.py`.
- `coaching-v2.css` asset URL'si `?v=0.15.2-coaching-2` olarak değiştirildi.
- `coaching-v2.js` asset URL'si `?v=0.15.2-coaching-2` olarak değiştirildi.
- Backend cache middleware'ine `GENESIS_COACHING_HOT_ASSET_CACHE_V1` kuralı eklendi.
- Aktif geliştirilen `/static/coaching-v2.js` ve `/static/coaching-v2.css` artık query parametresi olsa bile:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`
  döndürür.
- Böylece sonraki Koçluk Stüdyosu değişikliklerinin aynı sabit immutable cache sorunu nedeniyle görünmemesi engellendi.

Release:
- cache patch commit: 4155d17ddaa97a385fb83f9f00300cfadb2d75ca
- workflow doğrulama commit: f41b7fdba9b79fb11bad97d8c53d34417166427b
- deploy trigger commit: d197f05f0a594f387a1aada268cf35f1b20f74c6
- Fast Cloudflare Package Deploy run: 35861430658
- sonuç: SUCCESS
- Worker version ID: 38d23959-2051-4fab-91df-ab7edc14eb61
- Worker version number: 59
- Container version: 46
- Container image: registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:3512f2bc64094a76ac08c01ecf3209750ad7ee7cc54f511ed1062ab3c5b97a0b

Deploy smoke'a eklenen yeni zorunlu kontroller:
- canlı `coaching-v2.html` yeni JS/CSS query sürümünü içermeli
- canlı `coaching-v2.js?v=0.15.2-coaching-2` response header'ında `Cache-Control: no-store` bulunmalı
- canlı `coaching-v2.css?v=0.15.2-coaching-2` response header'ında `Cache-Control: no-store` bulunmalı
- bu kontroller geçmeden release SUCCESS sayılmaz

Bağımsız post-deploy inventory:
- main trigger commit: c0506b66c150a76c2b9942315f3da3d9f1bb652a
- Cloudflare GENESIS Inventory run: 35861901562
- sonuç: SUCCESS
- canlı source'ta `GENESIS_COACHING_HOT_ASSET_CACHE_V1` doğrulandı
- canlı HTML'de yeni JS/CSS asset sürümleri doğrulandı
- 23 kritik statik asset: HTTP 200
- 14 JavaScript syntax kontrolü: başarılı
- container failed instance: 0
- health errors: []
- observability logs: enabled

Bu olay production kodunun deploy edilmemesi değil, tarayıcı tarafında eski immutable assetlerin görünmeye devam etmesi problemiydi. Cache policy kalıcı olarak düzeltilmiştir.

## 15. 2026-09-23 GENESIS açılış Yönetim Paneli

Kullanıcının açık talebi:
- PNG/mockup üretilmeyecek; tasarım gerçek GENESIS WEB giriş sayfası olarak uygulanacak.
- Mevcut GENESIS koyu lacivert / mor görsel dili korunacak.
- Gereksiz görsel, yan menü, grafik ve kalabalık dashboard öğeleri olmayacak.
- Açılış ekranı üç sade panelden oluşacak:
  1. `Yönetim Paneli / Genel Bakış`
  2. `İşlemler / Seçim Yap`
  3. `Durum / Sistem`

Uygulanan mimari:
- Production patch dosyası: `cloudflare/home_dashboard.py`.
- Marker: `GENESIS_HOME_DASHBOARD_V1`.
- Ana `/` route'u mevcut GENESIS titlebar tasarımını koruyarak boş Yönetim Paneli görünümünü render eder.
- Panel gövdelerinde yalnız nötr boş durum metinleri bulunur: `Henüz veri yok` ve `Seçim yapılmadı`.
- Ayrı stil katmanı: `/static/genesis-home-dashboard-0.15.2.css?v=20260923-home-1`.
- Ana uygulama JS URL'si cache invalidation amacıyla `/static/app-0.10.7.js?v=20260923-home-1` olarak sürümlendi.
- Açılış ekranındaki başlık aksiyonları görsel placeholder olarak bırakıldı ve etkileşim dışı tutuldu.
- Önceki Konular / Konu Soruları / Testler çalışma alanı silinmedi; geriye dönük güvenlik için `/?workspace=1` üzerinden korunmaktadır.
- Backend, schema, R2/SQLite storage, auth veya coaching veri modeli değiştirilmedi.

İlk release denemesi:
- patch commit: `654cf71f859ed55c9f62a3b8722ddde275bc005e`
- workflow dashboard doğrulama commit: `05e91f94802b754e5ea5ed1985db585b5c558078`
- ilk trigger: `709a440bb17bec3fd85a5d1b4447afbadfe53491`
- Fast Cloudflare Package Deploy run: `35871205798`
- sonuç: FAILURE
- hata: Docker BuildKit `max depth exceeded`
- deploy adımı çalışmadığı için production etkilenmedi.

Kök neden ve release hattı düzeltmesi:
- Canlı base image zaten çok katmanlıydı; her production patch'i ayrı `COPY + RUN` Docker katmanı ekliyordu.
- Patch katmanları tek bir toplu `COPY` + tek bir toplu `RUN` altında birleştirildi.
- layer fix commit: `4414e0f62cba5f43e40e092489c8aefc3b63dc76`
- başarılı release trigger: `741f7554de9943745511166740c59917aee40028`

Başarılı production release:
- Fast Cloudflare Package Deploy run: `35871495303`
- sonuç: SUCCESS
- Worker version ID: `26942052-2d03-4e6c-a531-cd94892d8c4b`
- Worker version number: `60`
- Container version: `47`
- Container image: `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:2a4af72ce7b67c646777324bae1126686a59907c97ace04ff6c4bb4bb8a999fd`
- release smoke: SUCCESS
- single ADMIN auth, curriculum, Koçluk Stüdyosu, cache policy ve invalid-online-token kontrolleri korunarak geçti.

Bağımsız post-deploy inventory:
- inventory workflow doğrulama commit: `475a8efdb8216e3a6654a54407b22abf2a77690c`
- Cloudflare GENESIS Inventory run: `35872114484`
- sonuç: SUCCESS
- canlı source içinde dashboard HTML/JS/CSS marker'ları doğrulandı.
- root HTTP 200.
- health: 0.15.2 / schema 14 / storage ok / r2-fuse.
- `/api/auth/me`: authenticated ADMIN.
- invalid online token: HTTP 404.
- kritik statik assetler: 24/24 HTTP 200.
- kritik JavaScript syntax kontrolleri: 14/14 başarılı.
- container failed instance: 0.
- health errors: [].
- observability logs: enabled.

Bu geliştirme yeni fonksiyonel Adım 2 değildir; kullanıcı tarafından açıkça istenen GENESIS WEB açılış ekranı düzenlemesidir.

## 16. 2026-09-23 Yönetim Paneli stüdyo düğmeleri

Kullanıcının açık talebi:
- Yönetim Paneli içine alt alta üç düğme eklenecek:
  1. `Soru Stüdyosu`
  2. `Koçluk Stüdyosu`
  3. `Kurum Açma`
- Düğmeler ilgili mevcut GENESIS ekranlarını açacak.

Uygulanan davranış:
- `Soru Stüdyosu` → `/?workspace=1`
- `Koçluk Stüdyosu` → `/coaching`
- `Kurum Açma` → mevcut `window.genesisCreateInstitution()` kurum açma diyaloğu
- Düğmeler Yönetim Paneli'nin ilk sütununda dikey sırada yer alır.
- Dashboard marker: `GENESIS_HOME_DASHBOARD_V2`
- Asset sürümü: `20260923-home-2`

Release sırasında Cloudflare container image katman derinliği ve rollout tarafında birden fazla geçici hata görüldü. Production önce bilinen sağlam container tag'ına geri getirildi; ardından release hattı tek yeni Docker katmanı üretecek şekilde yeniden düzenlendi.

Başarılı final release:
- release workflow commit: `9baa7136899073c89ad199be38c74fe9e61598b2`
- release trigger: `82fa6187a16ae71cd348c920874a3ce0e4f8c9ea`
- Fast Cloudflare Package Deploy run: `35879661006`
- sonuç: SUCCESS
- Worker version ID: `e5c0fde8-10bb-4a13-8ec9-0bd48d593d75`
- Container rollout version: `55`
- Container image: `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:0e607006eb87456b2305bd6e10df6141e7e805129880d103107e888e3649c82e`
- production smoke: SUCCESS
- `Soru Stüdyosu`, `Koçluk Stüdyosu`, `Kurum Açma` metinleri ve yönlendirme/aksiyonları canlı JS içinde doğrulandı.
- `/?workspace=1` ve `/coaching` hedefleri release smoke kapsamındadır.
- single ADMIN, curriculum, Koçluk Stüdyosu cache policy ve invalid-online-token davranışları korunmuştur.

## 16. 2026-09-23 Yönetim Paneli stüdyo / kurum düğmeleri

Kullanıcının açık talebi:
- Yönetim Paneli içine alt alta üç düğme eklenecek:
  1. `Soru Stüdyosu`
  2. `Koçluk Stüdyosu`
  3. `Kurum Açma`
- Düğmeler ilgili mevcut GENESIS ekranlarını/akışlarını açacak.

Uygulanan kullanıcı davranışı:
- `Soru Stüdyosu` → `/?workspace=1` adresindeki mevcut Konular / Konu Soruları / Testler çalışma alanını açar.
- `Koçluk Stüdyosu` → `/coaching` sayfasını açar.
- `Kurum Açma` → mevcut `window.genesisCreateInstitution()` form akışını çağırır.
- Düğmeler Yönetim Paneli gövdesinde dikey olarak, mevcut GENESIS lacivert/mor tasarım diliyle gösterilir.

Production teknik çözümü:
- Container image katman derinliği artık yeni bir layer eklemeye izin vermediği için V2 dashboard değişikliği container içine güvenli şekilde yazılamadı.
- İlk denemelerde `max depth exceeded` ve Cloudflare image unpack / rollback davranışları doğrulandı.
- Bu nedenle container image'a dokunmadan Worker response katmanında UI overlay uygulanmıştır.
- Patch dosyası: `cloudflare/home_dashboard_edge.py`.
- Marker: `GENESIS_HOME_DASHBOARD_EDGE_V1`.
- Worker deploy workflow: `.github/workflows/cloudflare-worker-dashboard-overlay.yml`.
- Worker, yalnız `/` HTML yanıtına inline CSS + JS ekler; backend/storage/container içeriğini değiştirmez.
- Deploy `--containers-rollout=none` ile yapıldı ve container image/version'ın değişmediği workflow içinde doğrulandı.

Release:
- edge patch commit: `7b880a2c760bd46e513ed7cb301a2ad21e048a52`
- worker overlay workflow commit: `d8be3a85d0f3d3507bc2c7b22d87ff8c98bb4b1a`
- trigger commit: `7632d07720fecaeccd1a159bed4fc9a86ee0421f`
- Worker overlay deploy run: `35880765006`
- Worker deploy adımı: SUCCESS
- yeni Worker version ID: `cbd44c06-b95f-4851-869b-946066d30cd0`
- container image deploy öncesi/sonrası aynı: `sha256:0e607006eb87456b2305bd6e10df6141e7e805129880d103107e888e3649c82e`
- container version deploy öncesi/sonrası: `55`

İlk overlay workflow smoke sonucunda `/coaching` isteği cookie taşımadan yapıldığı için HTTP 403 görüldü; bu production regresyonu değildi. Gerçek tarayıcı akışındaki ADMIN session cookie'si smoke testine eklendi.

Bağımsız canlı HTTP doğrulama:
- smoke düzeltme commit: `166698d51cd1b8105794db8c605c9709d699c462`
- trigger commit: `b61b43fa6c931a06b412e4e629d5c73e461a9762`
- GENESIS Dashboard HTTP Smoke run: `35881051383`
- sonuç: SUCCESS
- root HTTP 200
- Worker overlay marker canlı
- Soru Stüdyosu, Koçluk Stüdyosu, Kurum Açma metinleri canlı root HTML'de doğrulandı
- Soru Stüdyosu yönlendirmesi doğrulandı
- Koçluk Stüdyosu yönlendirmesi doğrulandı
- `window.genesisCreateInstitution` form hook'u doğrulandı
- `/?workspace=1` HTTP 200
- ADMIN session ile `/coaching` HTTP 200

Not:
`Kurum Açma` düğmesi mevcut kurum formunu açar. Single-ADMIN güvenlik modunda kurum oluşturma backend işleminin HTTP 410 ile kapalı olması değiştirilmemiştir; kullanıcı yalnız ilgili ekranın açılmasını istemiştir.

## 17. 2026-09-23 Koçluk Stüdyosu sade dashboard yeniden tasarımı

Kullanıcının açık talebi:
- Önceki PNG konseptleri yalnız tasarım referansı olarak kullanılacak; yeni PNG üretilmeyecek.
- Koçluk Stüdyosu gerçek web dashboard'u sade, kullanımı kolay ve gereksiz düğmelerden arındırılmış biçimde yeniden düzenlenecek.
- Kullanıcının uzun vadeli hedefleri dashboard mimarisine yansıtılacak:
  - sınıf ve öğrenci yönetimi
  - ders / ünite / alt başlık sorumlulukları
  - PDF / test içerikleri ve Kolay-Orta-Zor düzeyi
  - otomatik haftalık ödev planı
  - bugün / hafta / geçmiş ödev görünümü
  - online sınav ve karne / analiz akışları

Production öncesi doğrulama:
- Canlı `coaching-v2.html` ve `coaching-v2.js` GitHub Actions üzerinden tekrar incelendi.
- Mevcut gerçek API ve fonksiyonlar doğrulandı:
  - `GET /api/coaching/v2/students`
  - `GET /api/coaching/v2/students/{id}/dashboard?week_start=...`
  - öğrenci ekleme
  - öğrenci ders / konu atama
  - haftalık plan
  - günlük sınav
  - performans analizi
- Önceki tarayıcı günlüğündeki `/api/coaching/v2/students/1/dashboard?week_start=2026-09-21` HTTP 500 kaydı ayrıca yeniden test edildi.
- GENESIS Coaching Dashboard API Smoke run: `35904129171`
- sonuç: SUCCESS; mevcut ilk öğrenci için aynı hafta dashboard endpointi HTTP 200 verdi.

Uygulanan dashboard:
- Worker-edge patch: `cloudflare/coaching_dashboard_edge.py`
- marker: `GENESIS_COACHING_DASHBOARD_EDGE_V1`
- container kaynaklarına, backend'e, schema'ya veya persistent storage'a dokunulmadı.
- Dashboard üç ana alandan oluşur:
  1. **Sınıflar ve Öğrenciler**
     - gerçek öğrenci listesi `/api/coaching/v2/students` üzerinden gelir
     - öğrenci arama
     - Öğrenci Ekle
     - seçili öğrenci
     - Ders Ata / Detay
     - Sınıf düğmesi gelecekteki sınıf veri modeline ayrılmıştır; sahte sınıf verisi üretilmez
  2. **Haftalık Çalışma Programı**
     - Bugün / Hafta / Geçmiş Ödevler
     - gerçek haftalık görevler ve online sınav atamaları dashboard API'sinden gösterilir
     - önceki / sonraki hafta ve Bu Hafta navigasyonu
  3. **Akademik Yapı ve Atamalar**
     - Dersler
     - Üniteler ve Alt Başlıklar
     - Sorumluluk Seçimi
     - İçerik Yüklemeleri
     - Otomatik Ödev Ayarı
     - Sınav ve Karne
- Mevcut ayrıntılı koçluk ekranı silinmedi.
- Ders / sorumluluk / sınav / analiz işlemlerinde mevcut `coaching-v2` çalışma alanı açılır ve `← Dashboard` ile yeni sade dashboard'a dönülür.
- Merkezi müfredat için mevcut `/static/coaching-curriculum.html` kullanılır.
- Henüz backend'i bulunmayan sınıf modeli ve Kolay-Orta-Zor otomatik ödev eşleştirmesi sahte veriyle taklit edilmedi; dashboard bu alanları gelecekteki fonksiyonel geliştirmeye hazır şekilde gösterir.

Teknik neden:
- Mevcut production container OCI layer zinciri yeni layer eklenmesinde daha önce `max depth exceeded` sınırına ulaşmıştır.
- Bu UI geliştirmesi bu nedenle container rollout yapılmadan Worker HTML response overlay olarak uygulanmıştır.
- Mevcut container image ve data katmanı korunmuştur.

Release:
- coaching dashboard edge patch commit: `d06765ab838c2fffa5e2ef737e30775c9c4ea069`
- Worker overlay workflow update: `df965ff369cac10d68908fc71832105fab874fa8`
- deploy trigger commit: `42f9f115da72b1e7190dec2a18de22bd0aeda699`
- GENESIS Worker Dashboard Overlay run: `35904421924`
- sonuç: SUCCESS
- Worker version ID: `2a2a844c-bf51-407b-a4ce-a71a99dc20f4`
- Worker version number: `73`
- Container version: `55`
- Container image: `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:0e607006eb87456b2305bd6e10df6141e7e805129880d103107e888e3649c82e`
- container failed instance: 0
- health errors: []
- observability logs: enabled
- Worker deploy `--containers-rollout=none`; container image/version deploy öncesi ve sonrası aynı doğrulandı.
- Production smoke içinde root dashboard, `/coaching`, yeni coaching marker, öğrenci API'si ve dashboard API'si doğrulandı.

Bu değişiklik mevcut koçluk dashboard'unun görsel/gezinti katmanıdır. Kullanıcının tarif ettiği sınıf veri modeli, içerik zorluk seviyesi, otomatik ödev motoru, PDF üzerinde kalemle sınav, optik ve öğrenci karne arşivi gibi yeni backend fonksiyonları ayrıca kullanıcı adımlarıyla geliştirilecektir.

## 18. 2026-09-23 22:22 UTC — VOLUME 1 production recovery

Kullanıcı talebi: “V3 recovery deploy’a devam et siteyi ayağa kaldır.”

### Kesinti ve doğrulanmış neden
- Handoff'ta devam ediyor görünen V3 docker-import run `35925159702` gerçekte FAILURE ile tamamlanmıştı.
- Tek katmanlı imaj oluşturma ve disposable model testi başarılıydı; Cloudflare runtime `ImagePullError / failed unpacking the image` bildirdi.
- Unpack hatasının daha alt düzey nedeni bu çalışmada belirlenmedi; yalnız layer sayısının bire indirilmesi sorunu çözmemiştir.
- Otomatik rollback, önceki `c4dea10a...` imajı için “no changes” döndürmüş; HTTP recovery doğrulaması yapmamıştı.
- Taze metadata run `35927570572`: Worker v80 `c058f345-5834-4438-b69c-5d1a527d65f8`, container v57. failed=0/errors=[] olmasına rağmen bağımsız smoke `35927669666` root HTTP 503 verdi. Hata sayılarının sıfır olması tek başına erişilebilirlik kanıtı değildir.

### Uygulanan kurtarma
- Yeni V3 imajı üretmek yerine son çalıştığı bağımsız smoke ile doğrulanmış v55 imaj digestine dönüldü:
  `sha256:0e607006eb87456b2305bd6e10df6141e7e805129880d103107e888e3649c82e`.
- Aktif Worker kaynağı hydrate edilerek korundu; ana sayfa ve Koçluk dashboard overlay marker'ları deploy öncesinde doğrulandı.
- R2 bucket `genesis-web-0152-data`, `GENESIS_DATA`, `GENESIS_CONTAINER`, instance tipi ve max_instances=1 korundu.
- Yeni şema geliştirmesi, production veri silme, veri geri yükleme veya yerel GENESIS aktarımı yapılmadı.
- Emergency workflow'a dry-run, config/binding doğrulamaları, beklenen digest + gerçek HTTP 200 + errors=[] + failed=0 kapısı ve cookie taşıyan API smoke eklendi.
- Recovery concurrency `cancel-in-progress: false` olarak ayarlandı.
- Workflow fix commit: `d3fbe34e4a4a2b193b9c818a96c463cf19559155`.
- Recovery trigger commit: `6ef1127b5184435a933ad51f9ccd7e5d4d72cc1e`.
- Emergency GENESIS Container Rollback run: `35927809215` — SUCCESS.
- Worker version: `333099cd-a686-4d97-8e31-df00ea4f0ebb` / number 81.
- Container rollout version: 61. Bu v55 numarasına dönüş değildir; eski sağlam imaj yeni rollout v61 olarak uygulanmıştır.
- Container failed=0, health.errors=[], observability.logs.enabled=true.

### Canlı doğrulama ve kapsam
- Root, `/?workspace=1`, `/coaching`: HTTP 200; iki dashboard overlay marker'ı mevcut.
- `/api/auth/me`: authenticated ADMIN, institution_id=null, must_change_password=false.
- `/api/system/health`: ok=true, version=0.15.2, schema=14, storage=ok, persistent_storage=r2-fuse, runtime=container.
- Curriculum tree ve coaching-v2 students: HTTP 200.
- Invalid online internet-test token: HTTP 404.
- Coaching JS/CSS: HTTP 200 ve `no-store, no-cache, must-revalidate, max-age=0`.
- V3 `/api/coaching/v3/classes` ve `/api/coaching/v3/curriculum`: HTTP 404. V3 model rollout'u başarılı veya tamamlanmış kabul edilmemelidir; site mevcut sağlam 0.15.2 işlevleriyle kurtarıldı.
- Öğrenci API'si `{"students":[]}`, müfredat API'si boş courses listesi döndürdü. Kesinti öncesi aynı andaki veri sayıları bilinmediği için veri kaybı veya tüm eski kayıtların korunduğu yönünde sonuç çıkarılamaz. Bu kurtarmada veri silme işlemi yapılmadı. Öğrenci olmadığı için öğrenci dashboard'u yeniden test edilmedi.
- Eski başarılı testlerin öğrenci bulunduğu varsayımı yeni duruma taşınmamalıdır.
- HTTP smoke'a süre sınırları eklendi ve öğrenci yanıt gövdelerinin Actions loglarına yazılması kaldırıldı.

Bu noktadan sonra kullanıcı yeni geliştirme istemeden yeniden V3 rollout yapılmayacak. Öncelik çalışan production'ın korunmasıdır.

## Adım durumu
Adım 1 kullanıcı tarafından ONAYLANDI ve kapatıldı.

Adım 1 sonucunda:
- merkezi Ders → Ünite → Alt Başlık modülü production'da hazır
- veri modeli hazır
- yetkilendirme hazır
- kalıcılık hazır
- toplu yükleme altyapısı hazır
- gerçek müfredat veri listesi henüz kullanıcı tarafından verilmediği için veri uydurulmadı

## Şu anki geliştirme noktası
2026-09-23 22:22 UTC VOLUME 1 recovery tamamlandı: site HTTP 200 ile erişilebilir. V3 import rollout başarısızdır; son sağlam 0.15.2 container imajı yeni rollout v61 ile geri getirildi. V3 API'leri 404; V3 tamamlanmış sayılmaz. Güncel öğrenci ve müfredat listeleri boş döndü; kesinti öncesi veriyle karşılaştırma yapılmadı. Ayrıntı ve sınırlar bölüm 18'dedir.
Adım 1 tamamlanmış durumda.
2026-09-23 production tam denetiminde bulunan doğrulanmış public-token ve online internet-test invalid-token hataları production'da düzeltildi ve bağımsız audit ile doğrulandı.
Canlı production health: 0.15.2 / schema 14 / storage ok / r2-fuse.
Güncel Worker: 333099cd-a686-4d97-8e31-df00ea4f0ebb (version number 81).
Güncel container version: 61.
GENESIS WEB kök açılış sayfası koyu lacivert/mor görsel dilde üç panelli Yönetim Panelidir. İlk panelde alt alta Soru Stüdyosu, Koçluk Stüdyosu ve Kurum Açma düğmeleri bulunur. Soru Stüdyosu `/?workspace=1`, Koçluk Stüdyosu `/coaching` hedefini açar; Kurum Açma mevcut kurum açma diyaloğunu çağırır. Önceki Konular / Konu Soruları / Testler çalışma alanı silinmemiştir.
Koçluk Stüdyosu artık sade üç alanlı yönetim dashboard'u ile açılır: Sınıflar ve Öğrenciler / Haftalık Çalışma Programı / Akademik Yapı ve Atamalar. Gerçek öğrenci listesi ve haftalık görev/sınav verileri mevcut coaching-v2 API'lerinden alınır. Ayrıntılı eski çalışma alanı silinmemiştir; ders, sorumluluk, sınav ve analiz işlemleri gerektiğinde aynı sayfa içinde açılır ve Dashboard'a geri dönülebilir. Henüz backend'i olmayan sınıf ve zorluk-düzeyi otomasyonları sahte veri üretmeden gelecekteki adımlar için ayrılmıştır. Koçluk Stüdyosu JS/CSS assetleri için uzun süreli immutable browser cache kapalıdır.
Bu UI geliştirmeleri Adım 2 olarak kabul edilmez; kullanıcı yeni fonksiyonel adımı ayrıca tarif etmeden yeni adım varsayılmayacaktır.
Production auth modu: kullanıcı adı/şifre olmadan otomatik tek ADMIN oturumu. Kurum kullanıcı hesapları kaldırılmıştır; kurum veri klasörleri korunmuştur.
TinyFish kullanılmayacak.
Ayrıca GENESIS web geliştirme sohbetlerinin otomatik devir sistemi için Chrome uzantısı geliştiriliyor.

## Yeni ChatGPT sohbetine talimat
- Bu dosyayı tek gerçek handoff kaynağı olarak kullan.
- Kullanıcının tekrar geçmişi anlatmasını isteme.
- Önce mevcut production durumunu bozma.
- Kullanıcı yeni adımı tarif etmeden fonksiyonel Adım 2'yi varsayma.
- Bir hata varsa önce mevcut adımı düzelt.
- Her önemli değişiklikten sonra bu handoff dosyasını ve GENESIS_WEB_ERROR_LOG.md dosyasını güncelle.
