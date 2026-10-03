# GENESIS soru havuzu — kalıcı veri sözleşmesi

1 Ekim 2026 tarihli son kullanıcı düzeltmesi geçerlidir: **kullanıcı** konu/test
klasörlerini, sınavları ve soruları açık arayüz/API isteğiyle silebilir,
düzenleyebilir ve taşıyabilir. Kullanıcının dışında başlangıç, temizlik,
arka plan, geliştirme ve yayın işlemleri bu kayıtları veya varlıklarını
silemez/değiştiremez. Önceki mutlak kilit talimatı bu düzeltmeyle değişmiştir.
Üretimde kabul kaydı oluşturulmaz.

## Uygulama davranışı

- Silme, düzenleme ve taşıma düğmeleri açıktır; silme onayı korunur. Dolu
  klasör ve kullanılan soru için mevcut bağımlılık kontrolleri uygulanır.
- Havuz yazma isteği mevcut oturuma bağlı kullanıcı izin belirtecini taşır.
  Oturumsuz, belirteçsiz ve çapraz site yazmalar engellenir. Otomatik temizlik
  uç noktası kapalı kalır. Belirteç oturum anahtarı veya havuz verisi içermez.
- SQL yetkilendirmesi/tetikleyiciler HTTP dışındaki otomatik yazmaları
  engeller. Kullanıcı değişiminin önce/sonra satırı **aynı SQLite işlemi**
  içinde eklemeli denetim kaydına yazılır; rollback kaydı da geri alır.
- Snapshot kontrolü mevcut merkezi verilerden yeni snapshot'a bütün
  değişimleri bu kayıt zinciriyle karşılaştırır. Kayıtsız değişim yayınlanamaz.
- Kullanıcı soru silince bağlı kesim ve görsel silme niyeti kaydedilir.
  Merkezi DB aktarılmadan görsel silinmez. Paylaşılan kaynak ve hâlâ kullanılan
  görsel korunur. Geçici yerel dosya kaybı silme izni sayılmaz.
- Başarılı yanıt ilgili DB/dosya R2 işlemleri tamamlanınca verilir. Aktarım
  hatası başarıya çevrilmez. Başlangıç yalnızca güncel merkezi DB'yi okur;
  kaydedilmiş kullanıcı silme niyetlerini tamamlar. Silinen sorular ve eski
  Drive havuzu geri yüklenmez. Snapshot geçmişi otomatik yüklenmez.
- Tüm cihazlar aynı sunucu havuzunu okur. Yanıtlar `no-store`; revizyon beş
  saniyede bir ve pencereye dönüldüğünde kontrol edilir. Açık düzenleme formu
  kesilmeden, kapatıldıktan sonra güncel havuz gösterilir. Frontend sürümü
  eski tarayıcı önbelleklerinin kilitli düğmeleri göstermesini önler.

## Depolama

| Amaç | Konum |
| --- | --- |
| Çalışan SQLite | Container'ın yerel `/app/DATA/genesis.db` dosyası |
| Merkezi soru snapshot'ı | R2 `DATA/genesis.db` |
| Oturum ve koçluk snapshot'ı | R2 `_runtime/operations.db` |
| Soru görselleri ve kaynaklar | R2 `DATA/DisplayImages/`, `DATA/RawCrops/`, `DATA/Sources/` |
| İçerik adresli soru snapshot geçmişi | R2 `_snapshots/question-pool/<revision>.db` |
| İlk onarımın koruma kopyası | R2 `_recovery/20260930/DATA/` |

Container değişince merkezi snapshot geri okunur. Oturum/koçluk snapshot'ından
soru tabloları içe aktarılmaz. Ana snapshot güncellemesinde R2 ETag koşulu,
başka bir havuz revizyonunun eski kopyayla üzerine yazılmasını engeller.
Drive varsa ikincil kopyadır; eski silinmiş soru havuzu geri getirilmez.

## GENESIS çekirdek-only yayın kuralı

ANA PRG veya Koçluk kapsam dışı bırakıldığında `[core-only]` yayın yolu
kullanılır. Bu yol yeni bir container image seçmez; o anda gerçekten production'da
çalışan doğrulanmış image'ı korur ve yalnız Worker/UI katmanındaki çekirdek değişikliği
yayınlar. Ertelenmiş Koçluk endpoint'leri core release gate'ine dahil edilmez.
Worker-only değişiklik container restart/boot-id değişimi gerektirmez.

Rollback, core patch'i yeniden uygulamaz; yayın öncesi Worker kaynağına geri döner.
Başarılı `[pool-restore]` sonrasında `runtime-activation-image.txt` doğrulanmış
restore image digest'iyle otomatik senkronlanır. Böylece eski candidate image'ın
sonraki yayında yanlışlıkla seçilmesi engellenir.

## Geliştirme ve yayın

Tek etkin üretim yolu `.github/workflows/cloudflare-runtime-recovery.yml`'dir.
Koruma denetimini atlayan eski Cloudflare yayın/rollback işleri kapatılmıştır.
Salt okunur envanter ve uygulamanın diğer paket yayınları etkilenmez.

1. Exact canlı Worker ve image alınır; mevcut DB ve R2 varlıkları salt okunur
   olarak karşılaştırma için kaydedilir.
2. `[pool-candidate]` ile geçici SQLite/R2, kullanıcı düzenleme/silme, otomatik yazma engeli, R2 yeniden başlangıç ve gerçek kaynak-kesim-kayıt API akışı
   ve iki bağımsız Chromium profili kontrol edilir. Üretim havuzuna test
   kaydı eklenmez. Yerel UI kontrolünde yalnızca revizyon taşıma yanıtı
   gerçek geçici DB fingerprint'iyle benzetilir; R2/restart akışı ayrıca
   bellek nesne deposu kabul kontrolüyle doğrulanır.
3. Başarılı candidate'ın image kimliği `runtime-activation-image.txt` içine
   yazılır. `[pool-release]` canlı yayını ve üretim kontrolünü çalıştırır.
4. Önce/sonra DB ve R2 parmak izleri, root/auth/koçluk, iki oturum ve yeni
   container başlangıcı doğrulanır. Başarısızlıkta exact önceki image/Worker
   otomatik geri alınır; veritabanı eski kopyayla değiştirilmez.

Bu korumalar uygulama ve yayın süreçlerinin yanlışlıkla veri değiştirmesini
engeller. Hesap sahibinin Cloudflare'de doğrudan nesne silmesi veya koddan
korumaları bilerek kaldırması için mutlak bir engel değildir.

## Tarihli program geri yükleme noktası

`genesis-restore-2026-10-01`: tam v115 image ve exact Worker şifreli kalıcı
pakette saklanır. `cloudflare/restore-points/README.md` geri yükleme yoludur.
`[pool-checkpoint]` yalnızca kayıt alır; `[pool-restore]` aynı korumalı yayın
kapılarından geçer. Her geri yükleme, işlem anındaki **güncel** DB/R2 parmak
izlerini korur. Tarihli kanıt DB'si geri yüklenmez; anahtar/arşiv silinmez.

## Devir belgesindeki güncellenmiş bulgular

Eski `c4dea10...` image ve container lifecycle hata açıklaması güncel değildir.
Önceki onarımda yerel SQLite/R2 snapshot depolaması, bloklamayan oturum işlemleri,
doğrulanmış container başlangıcı ve az katmanlı image ile açılmama sorunu
giderildi. Çalışan v113 image soru koruması değişikliği için temel alınmıştır.
Canlı kabul sonucu ve yayın kimliği, son kontrol raporuna yazılır.
