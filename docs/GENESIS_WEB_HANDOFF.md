# GENESIS WEB — GÜNCEL GELİŞTİRME DEVİR DOSYASI

> Bu dosya yeni ChatGPT geliştirme sohbetlerinin başlangıç bağlamıdır.
> Her önemli web geliştirme/deploy aşamasından sonra güncellenmelidir.

## Protokol
- Geliştirme adım adım yürütülür.
- Bir adım kullanıcı tarafından onaylanmadan sonraki adıma geçilmez.
- TinyFish kotası gereksiz yere tüketilmez.
- GitHub mümkün olduğunca paket/deploy köprüsü olarak kullanılır.
- Production yapısı tahmin edilmez; önce canlı yapı doğrulanır.
- Yerel GENESIS ile web GENESIS birbirinden ayrıdır; kullanıcı açıkça istemedikçe yerelden web'e aktarım yapılmaz.

## Proje
- GitHub: yllbay/YILBAY-OGRENCI-TAKIP
- Production Worker: genesis-web-0152
- Production URL: https://genesis-web-0152.yilbayonurcelik.workers.dev/
- Uygulama sürümü: 0.11.2
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
Kullanıcı bir sonraki fonksiyonel geliştirme adımını henüz tarif etmedi.
Ayrıca GENESIS web geliştirme sohbetlerinin otomatik devir sistemi için Chrome uzantısı geliştiriliyor.

## Yeni ChatGPT sohbetine talimat
- Bu dosyayı tek gerçek handoff kaynağı olarak kullan.
- Kullanıcının tekrar geçmişi anlatmasını isteme.
- Önce mevcut production durumunu bozma.
- Kullanıcı yeni adımı tarif etmeden fonksiyonel Adım 2'yi varsayma.
- Bir hata varsa önce mevcut adımı düzelt.
- Her önemli değişiklikten sonra bu handoff dosyasını ve GENESIS_WEB_ERROR_LOG.md dosyasını güncelle.
