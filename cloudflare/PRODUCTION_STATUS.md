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
