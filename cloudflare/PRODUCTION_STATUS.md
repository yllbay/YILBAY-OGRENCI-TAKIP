# 3 Ekim 2026 — GENESIS çekirdek V4 production doğrulaması

ANA PRG ve Koçluk kapsam dışı kalmaya devam ediyor. GENESIS çekirdek + Soru
Stüdyosu için native ana ekran, edge ana ekran ve storage sync onarımları
production'da doğrulandı.

- Production release run: `37154751125` — **success**.
- Worker version: `c83de3ff-0627-4715-9b38-98aa9428b676`.
- Aktif container image:
  `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:756f364a2babe47248e0b5ff2e837eb306c27e0dd4d8e67a35b57f6c45a154c5`.
- Native home installer mevcut V1/V2 helper'ı idempotent olarak güncelliyor; kaldırılmış
  close handler nedeniyle Soru Stüdyosu binding'i artık kırılmıyor.
- Edge home overlay V4'e yükseltildi; eski V1/V2/V3 payload'daki çift
  `const close` bildirimi tamamen kaldırıldı.
- Ana ekranda yalnız doğrulanmış Soru Stüdyosu aksiyonu gösteriliyor.
- Background storage taraması 30 saniyeye çıkarıldı; başarılı kullanıcı yazısı
  sonrasında gereksiz ikinci tam-tree taraması yapılmıyor, hata durumunda anlık retry korunuyor.
- Değişmemiş dosyalar stat signature ile hash/R2 işinden atlanıyor.
- Candidate run `37153671999` — **success**; gerçek PDF upload → crop → bbox →
  save-one/finalize, CRUD, iki oturum, splitter, narrow viewport ve storage retry testleri geçti.
- Production: container restart doğrulandı.
- Production: SQLite + R2 protected fingerprints değişmedi.
- Production: gerçek ana ekran → Soru Stüdyosu navigation/splitter/revision browser testi geçti.
- Rollback tetiklenmedi.
- Production UI gate artık eski sabit cache etiketi yerine versioned JS URL ve güncel
  `GENESIS_QUESTION_POOL_USER_OWNED_V2` / dashboard marker içeriğini doğruluyor.
- CI'da Playwright Chromium cache eklendi; sonraki doğrulamalarda tekrar indirme maliyeti azaltıldı.

# 3 Ekim 2026 — GENESIS çekirdek kapsamı doğrulandı

ANA PRG ve Koçluk geliştirmeleri kullanıcı talimatıyla ertelendi. Production,
doğrulanmış v115 container image üzerinde tutuluyor; ana ekranda yalnız
doğrulanmış **Soru Stüdyosu** aksiyonu gösteriliyor. Ertelenmiş Koçluk ve
backend karşılığı olmayan Kurum Açma butonları ana ekrandan kaldırıldı.

- Core-only production run: Actions `37148350994` — **success**.
- Worker version: `72ea2ddd-b09a-46b6-84ca-627b2c2e6586`.
- Container image değişmedi:
  `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:520be26036aede569368ed985a114e4220b022baf7bf7a8679579e0fd4d822d6`.
- Disposable kullanıcı klasör/soru/sınav düzenleme-silme + iki oturum: geçti.
- Chromium splitter/iki profil/refresh testi: geçti.
- Core-only Worker değişikliğinde container restart zorunluluğu kaldırıldı.
- Production SQLite ve R2 fingerprint'leri önce/sonra aynı kaldı.
- Production Soru Stüdyosu navigation/splitter/revision testi geçti.
- Rollback tetiklenmedi.
- Restore sonrası stale activation-image işaretçisi v115'e düzeltildi;
  gelecekte başarılı restore, activation pointer'ını otomatik senkronlar.
- Core-only release mevcut production image'ını kullanır; ANA image veya
  ertelenmiş Koçluk endpoint'leri release gate'i değildir.

# Güncel üretim — kullanıcıya ait soru havuzu

**01.10.2026 geri yükleme noktası kaydedildi:**
[`genesis-restore-2026-10-01`](https://github.com/yllbay/YILBAY-OGRENCI-TAKIP/releases/tag/genesis-restore-2026-10-01).
Exact v115 image/Worker ve tam bağımlılık katmanları şifreli 280.064.032 baytlık
pakette saklandı. [Kayıt işi 36784793384](https://github.com/yllbay/YILBAY-OGRENCI-TAKIP/actions/runs/36784793384)
başarılı; üretim kodu yeniden yayınlanmadı, DB/R2 parmak izleri değişmedi.
Manifest: `cloudflare/restore-points/2026-10-01.json`.
Geri yükleme: `python cloudflare/restore_checkpoint.py 2026-10-01 --apply`;
yalnızca korumalı akış, **güncel** soru havuzu korunur. Ayrıntılar
`cloudflare/restore-points/README.md`. Tarihli DB rollback yapılmaz.

**1 Ekim 2026: v115 başarıyla yayınlandı.** Son kullanıcı talimatı mevcut
klasör/sınav/soruların kullanıcı tarafından silinmesine ve düzenlenmesine
izin verir; otomatik, başlangıç, temizlik, geliştirme ve yayın yazmaları
engellenmeye devam eder. Önceki mutlak kilit kaldırılmıştır.

- [Korumalı yayın 36783274326](https://github.com/yllbay/YILBAY-OGRENCI-TAKIP/actions/runs/36783274326): success.
- [Geçici arayüz kabulü 36782971033](https://github.com/yllbay/YILBAY-OGRENCI-TAKIP/actions/runs/36782971033): success.
- Image: `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:520be26036aede569368ed985a114e4220b022baf7bf7a8679579e0fd4d822d6`.
- Worker: `c742c1dd-e3f4-4256-a2bd-331ff29a7126`; politika `GENESIS_QUESTION_POOL_USER_OWNED_V2`.
- Önce/sonra: topics=2, questions=5, finalized crops=5, sources=1.
- DB SHA-256: `175073c407d5d5b691c2a95f211cfe2ff170d8798dea4cf1d31d098b6eedd7b8`.
- R2 varlık SHA-256: `6882b92182ac93435ab1b0146f9f62f5229c0a3ab6d4fc439b1f030c6a1cc66d`; 14 nesne, ETag eşit.
- R2 geri okuma, iki oturum ve canlı arayüz passed; last_error=null, pending=false.
- Üretimde kabul verisi oluşturulmadı/silinmedi; rollback gerekmedi.
- Geçici ortamda gerçek kullanıcı silmeleri ve diğer profilde yenileme,
  SQL otomatik yazma engeli ve R2/restart kalıcılığı geçti.
- Ayrıntılı yerel kanıt: `outputs/user-pool-permissions-20261001`.

Aşağıdaki v114/boş havuz sonuçları **önceki yayın tarihine aittir**, güncel
veri envanteri değildir. Sonraki yayında mevcut canlı image ve veriler
başlangıç alınır. Veritabanı eski kopyayla geri alınmaz.

---

# Doğrulanmış canlı sürüm — 1 Ekim 2026

Production: https://genesis-web-0152.yilbayonurcelik.workers.dev/

Soru Stüdyosu: https://genesis-web-0152.yilbayonurcelik.workers.dev/?workspace=1

## Yayın kimliği

- Başarılı candidate: Actions `36776973700`, kaynak commit `cd49d9b1a1ed86e64a0fa2534fed070e0fa90c2b`.
- Başarılı production: Actions `36777363096`, yayın commit `986f9c084c685c247e6491237ea49f196f86976c`.
- Worker version: `736290a0-6e08-45dc-8701-a692b249f5d9`.
- Container app version: `114`, failed instance `0`, health errors `[]`.
- Çalışan image:
  `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer@sha256:69f13459783ad864f5e3b36b1cc70cef95ff888a49b41b1abb312d45b5a0d4f9`.
- Önceki çalışan v113 image, ilk yayın için saklanan geri dönüş noktası:
  `registry.cloudflare.com/25fb323918fd4c2d4794fe7a98da6800/genesis-web-0152-genesiscontainer:runtime-recovery-437814558861`.

Sonraki yayında o anda çalışan image baseline alınmalıdır. Eski image'a
elle dönüş yapılmamalıdır; veri koruması ve şema uyumluluğu gate'ten geçmelidir.
Üretim DB'si hiçbir koşulda image rollback ile eski kopyaya çevrilmez.

## Sonuçlar

- Root, gerçek ana sayfadan Soru Stüdyosu bağlantısı, auth ADMIN, koçluk ve
  belirtilen API'ler 200; hatalı online test token'ı 404.
- Container değişimi sonrası R2 snapshot geri okundu. Sağlık durumu `ok=true`,
  `restored=true`, `last_error=null`, `pool_pending=false`.
- Protected DB SHA-256 önce/sonra:
  `17f0c5c0dc6025000cd3457763aa0355f3c5951cbaa5dc9d90223be194b4e12a`.
- R2 korumalı varlık fingerprint'i önce/sonra:
  `500284f14626931d62adac6303b5bd53be466f1c6291d6b92f312fc88306454d`, nesne sayısı `3`.
- İki bağımsız gerçek production oturumu aynı revizyonu gördü.
- Canlı tarayıcıda splitter 16 px; sürükleme genişliği 60 px değiştirdi;
  JavaScript sayfa hatası yok. Havuzda değişiklik yapan UI işlemi çalıştırılmadı.
- Ek bağımsız kontrolde 39 salt okunur istek başarılı; oturum/koçluk okuma
  akışları boyunca ana R2 DB ETag'i değişmedi.
- Otomatik rollback tetiklenmedi. Geçici salt okunur audit Worker kaldırıldı.

Geçici ortamda gerçek kaynak yükleme, PDF kesimi, stored bbox kullanımı,
finalize, RAW/gösterim dosyalarının korunması, iki oturumda soruyu görme,
klasör ekleme, eski soru/klasör silme-değiştirme engeli ve test klasörü
koruması geçti. Bellek R2 deposunda yeni çalışma ortamına geri yükleme ve
koçluk/oturum yazılarının soru snapshot'ını değiştirmemesi geçti. Chromium'da
iki profil arasında otomatik klasör yenileme ve dar ekranda scrollbar kontrolü geçti.

**Veri durumu:** canlı baseline ve son kontrolde `topics=0`, `questions=0`.
Bu geliştirme sırasında üretimde soru/klasör oluşturulmadı veya silinmedi.
Eski silinmiş Drive soruları geri getirilmedi. Üç R2 varlığı klasör işaretleridir;
geçmiş gerçek PNG/PDF sorularının varlığı veya kurtarıldığı ileri sürülmemektedir.

Uygulama veri sözleşmesi: [QUESTION_POOL_CONTRACT.md](QUESTION_POOL_CONTRACT.md).
Yerel ayrıntılı kanıtlar çalışma alanında `outputs/question-pool-20260930` altındadır.
