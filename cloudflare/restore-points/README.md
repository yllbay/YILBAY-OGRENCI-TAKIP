# GENESIS geri yükleme noktası — 01.10.2026

Kimlik: `genesis-restore-2026-10-01`, doğrulanmış container **v115** ve Worker
`c742c1dd-e3f4-4256-a2bd-331ff29a7126`.

Kalıcı paket: [GitHub Release](https://github.com/yllbay/YILBAY-OGRENCI-TAKIP/releases/tag/genesis-restore-2026-10-01).
Release etiketi kaynak kodu sabitler. Şifreli paket tam OCI image/dependency
katmanlarını, exact Worker modülünü, uyumluluk ayarlarını, başlangıç betiğini,
uygulama kaynaklarını ve SHA-256 envanterini içerir. Image registry'den
kalksa bile paket aynı manifest/image digest'iyle geri yüklenebilir.
Üç günlük Actions artifact'ına bağımlı değildir. Arşiv şifrelenmiştir;
anahtar `GENESIS_RESTORE_20261001_KEY` Actions secret'ında ve yerel
`outputs/restore-points/2026-10-01/restore.key` dosyasında tutulur.
Anahtar ve çözülmüş paket açık repository'ye eklenmez.

## Geri dönüşün kapsamı

**Program paketi geri alınır; o anda güncel olan soru havuzu korunur.**
Snapshot tarihindeki soru sayıları/parmak izleri yalnızca kanıttır. R2
`DATA/genesis.db`, görseller, kaynaklar, klasörler ve sonradan yapılan kullanıcı
ekleme/silme/düzenlemeleri eski kopyayla değiştirilmez. Paket üretim DB yedeği
içermez. Güncel ortam değişkenleri/secret'lar `--keep-vars` ile korunur.
Drive'dan eski veri yüklenmez, seed/cleanup çalıştırılmaz.

## İleride geri yükleme

Aktif `cloudflare-release` branch'inde, temiz ve uzak branch ile güncel checkout:

```powershell
python cloudflare/restore_checkpoint.py 2026-10-01 --apply
```

Bu komut yalnızca `[pool-restore]` talebini korumalı
`cloudflare-runtime-recovery.yml` akışına iletir. Yerelde DB yazmaz, git reset
yapmaz veya Cloudflare'e doğrudan yayın yapmaz. `--apply` olmadan yalnızca
seçilen paket gösterilir. Geri yükleme talebi tek başına başarı kanıtı değildir;
Actions sonucu ve üretim gate'i tamamlanmalıdır.

Akış sırayla:

1. O anda çalışan image/Worker ve **güncel** DB/R2 parmak izlerini alır.
2. Commit'teki manifest'e göre şifreli arşiv ve bütün dosya hash'lerini kontrol eder.
3. Tam kaydedilmiş image ve Worker'ı seçer. Registry kaybında exact OCI kopyasını yükler.
4. Geçici container/verilerde mevcut kullanıcı arayüzü/API kabulünü çalıştırır.
5. Korumalı yayından sonra güncel DB/R2 varlık eşitliğini ve uygulamayı doğrular.
6. Başarısızlıkta işlemden hemen önceki exact image/Worker geri alınır;
   veritabanı geri alınmaz. Uyum kontrolünü atlamak yasaktır.

Kayıt oluşturma `[pool-checkpoint]` ile salt okunur gerçekleşir; kod yayını,
container yeniden başlangıcı veya üretim kabul kaydı oluşturmaz. Aynı etiketli
Release yeniden yazılmaz. Yeni paket için yeni tarih/kimlik gerekir.
