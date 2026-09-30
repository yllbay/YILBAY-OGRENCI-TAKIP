# GENESIS soru havuzu — kalıcı veri sözleşmesi

30 Eylül 2026 tarihli son kullanıcı talimatı geçerlidir: kayıtlı soru, konu
klasörü, test klasörü ve soru varlıkları değiştirilemez veya silinemez.
Önceki devir belgesindeki üretimde geçici soru oluşturup silme senaryosu bu
talimatla geçersizdir. Kabul verileri yalnızca geçici ortamda oluşturulur.

## Uygulama davranışı

- Yeni klasör, kaynak ve soru eklemek açıktır. Mevcut soru/klasör düzenleme,
  taşıma ve silme istekleri HTTP 423 ile engellenir.
- SQLite bağlantı yetkilendirmesi ve veritabanı tetikleyicileri, HTTP katmanı
  dışındaki eski otomatik işlemlerin de kayıtlı içeriği değiştirmesini engeller.
- Tamamlanan kesimin koordinatları, RAW görseli, gösterim görseli ve kaynak
  dosyası korunur. Otomatik başlangıç ve dosya temizliği kaldırılmıştır.
- Soru kaydının başarılı yanıtı, ilgili dosyalar ve güvenli DB snapshot'ı R2'ye
  aktarılınca gönderilir. Aktarım tamamlanmazsa başarı yanıtı verilmez.
- Yerel dosyanın kaybolması R2 nesnesini silmez. Korumalı dosya R2'den geri okunur.
- Soru havuzu tarayıcıya ait bir DB veya yerel önbellek üzerinden sunulmaz.
  API yanıtları `no-store` kullanır; sunucu revizyonu beş saniyede bir ve
  pencereye dönüldüğünde kontrol edilir. Açık kesim/düzenleme formu kesilmeden,
  kapatıldıktan sonraki kontrolde güncel havuz gösterilir.

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

## Geliştirme ve yayın

Tek etkin üretim yolu `.github/workflows/cloudflare-runtime-recovery.yml`'dir.
Koruma denetimini atlayan eski Cloudflare yayın/rollback işleri kapatılmıştır.
Salt okunur envanter ve uygulamanın diğer paket yayınları etkilenmez.

1. Exact canlı Worker ve image alınır; mevcut DB ve R2 varlıkları salt okunur
   olarak karşılaştırma için kaydedilir.
2. `[pool-candidate]` ile geçici SQLite/R2, gerçek kaynak-kesim-kayıt API akışı
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

## Devir belgesindeki güncellenmiş bulgular

Eski `c4dea10...` image ve container lifecycle hata açıklaması güncel değildir.
Önceki onarımda yerel SQLite/R2 snapshot depolaması, bloklamayan oturum işlemleri,
doğrulanmış container başlangıcı ve az katmanlı image ile açılmama sorunu
giderildi. Çalışan v113 image soru koruması değişikliği için temel alınmıştır.
Canlı kabul sonucu ve yayın kimliği, son kontrol raporuna yazılır.
