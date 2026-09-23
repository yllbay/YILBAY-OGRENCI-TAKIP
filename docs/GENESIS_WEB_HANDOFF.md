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
- Son doğrulanmış Worker version ID: c37ee267-f427-4b8d-b00f-6aabd4062d4d
- Son doğrulanmış Worker version number: 53
- Son doğrulanmış container version: 40
- Son doğrulanmış container image: registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:74b1f284bc7a8a2035a0392291d6c41c60e861cb8ef0c849490579601c9b261a

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
Adım 1 tamamlanmış durumda.
2026-09-23 production tam denetiminde bulunan doğrulanmış public-token ve online internet-test invalid-token hataları production'da düzeltildi ve bağımsız audit ile doğrulandı.
Canlı production health: 0.15.2 / schema 14 / storage ok / r2-fuse.
Güncel Worker: c37ee267-f427-4b8d-b00f-6aabd4062d4d.
Güncel container version: 43.
Kullanıcı bir sonraki fonksiyonel geliştirme adımını henüz tarif etmedi.
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
