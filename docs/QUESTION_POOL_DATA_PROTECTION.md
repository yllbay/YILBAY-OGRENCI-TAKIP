# GENESIS Soru Havuzu Veri Koruma Politikası

Tarih: 2026-09-28

## Değişmez mimari kural

GENESIS soru havuzu cihazdan, tarayıcıdan ve uygulama sürümünden bağımsız tek bir production veri havuzudur.

Production erişim adresi:
- https://genesis-web-0152.yilbayonurcelik.workers.dev/?workspace=1

Ana kalıcı veri:
- Cloudflare R2 bucket: genesis-web-0152-data
- R2 DATA/genesis.db
- R2 DATA/DisplayImages/
- R2 DATA/DeletionTombstones/

İkinci kalıcı kopya:
- Google Drive soru PNG kopyaları / snapshot yedekleri.

## Silme semantiği

Bir soru yalnız kullanıcının açık DELETE isteğiyle kalıcı olarak silinebilir.

DELETE /api/questions/{question_id}:
1. questions satırını siler.
2. R2 DATA içindeki raw/display görüntüsünü siler.
3. Yerel legacy backup ZIP kopyalarından soruyu ayıklar.
4. Drive snapshot yedeklerinden soruyu ayıklar.
5. questions.drive_file_id ile bağlı Google Drive soru dosyasını siler.
6. Her kalıcı kopya temizlenene kadar R2 DATA/DeletionTombstones altında dayanıklı silme kaydı tutulur.
7. Drive/R2 geçici olarak erişilemiyorsa tombstone sonraki backend başlangıcında tekrar işlenir.

Sınavlarda kullanılan soru doğrudan silinmez; önce sınav referanslarının kaldırılması gerekir.

## Geliştirme / deploy koruması

- Development, canary, UI overlay ve test adımları production soru verisini temizleyemez.
- Startup otomatik depolama temizliği varsayılan olarak kapalıdır.
- GENESIS_STARTUP_STORAGE_MAINTENANCE yalnız açıkça 1 verilirse eski bakım temizliği çalışabilir; production geliştirme deploylarında 1 verilmez.
- Açık kullanıcı silme tombstone işlemleri startup'ta çalışmaya devam eder; bu bir bakım silmesi değil kullanıcının daha önce verdiği silme talebinin tamamlanmasıdır.
- Worker-only UI deployları container rollout yapmadan uygulanır.
- Container image değişiklikleri R2 DATA'yı paketlemez, sıfırlamaz veya üzerine genesis.db kopyalamaz.
- Google Drive soru kopyaları geliştirme/test amacıyla topluca silinmez veya yeniden oluşturulmaz.
- Test verileri production soru havuzundan ayrıdır.
- Şema değişiklikleri destructive reset yerine migration ile yapılır.

## Production guard

Aktif guard marker:
- GENESIS_QUESTION_POOL_GUARD_V1

Aktif guard container image:
- genesis-web-0152-genesiscontainer:question-pool-guard-2cdf91e290f8

Production activation:
- workflow: GENESIS Question Pool Guard Activate
- run: 36476929683
- result: SUCCESS
- container version: 64
- failed instances: 0
- health errors: 0
- read-only production smoke: GENESIS_QUESTION_POOL_GUARD_PRODUCTION_OK

## Gelecekteki geliştirmeler için zorunlu kural

Kod, arayüz, Worker ve container değişebilir. Kullanıcı tarafından kaydedilmiş soru havuzu değişikliklerden bağımsız kalır.

Production R2 veya Drive soru verisini değiştirecek her yeni kod yolu:
- açık kullanıcı veri işlemi olmalı,
- audit kaydı üretmeli,
- hata durumunda sessiz başarı vermemeli,
- mümkünse dayanıklı retry/tombstone kullanmalı,
- release öncesi read-only production smoke ile doğrulanmalıdır.
