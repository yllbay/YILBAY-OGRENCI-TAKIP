# Cloudflare CI/CD — GENESIS

Bu klasör, `genesis-web-0152` için GitHub Actions + Wrangler deployment hattının kontrol alanıdır.

## Güvenlik modeli

- Production deploy otomatik push ile çalışmaz.
- Workflow yalnız `workflow_dispatch` ile elle tetiklenir.
- Önce `inventory` çalışır ve Cloudflare'daki mevcut Worker ayarlarını salt-okunur biçimde doğrular.
- Secret değerleri çıktı veya artifact içine yazılmaz.
- Deploy için ikinci bir açık onay gerekir: `DEPLOY_GENESIS_WEB_0152`.
- Gerçek production `wrangler.production.jsonc` ve `Dockerfile` mevcut canlı Worker/container mimarisiyle eşleştirilmeden deploy job'u bilinçli olarak durur.

## Gerekli GitHub repository secrets

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

API token için önerilen minimum kapsam: mevcut `genesis-web-0152` Worker üzerinde **Editor**. Container deployment için hesabın mevcut container kullanımına göre **Containers Edit** de gerekebilir. Route/custom-domain değiştirilmiyorsa Workers Routes izni eklenmemelidir.

## İlk çalıştırma

1. İki GitHub secret'ı ekleyin.
2. Actions > **Cloudflare GENESIS Production** > Run workflow.
3. `mode=inventory` seçin.
4. Oluşan güvenli inventory çıktısı ile canlı Wrangler/Container yapılandırmasını repo içinde birebir kurun.
5. Testlerden sonra `mode=deploy`, confirmation=`DEPLOY_GENESIS_WEB_0152` ile production deploy çalıştırın.

## Neden önce inventory?

Mevcut canlı Worker bir Container katmanı kullanıyor. Cloudflare Containers deploy'u Worker kodu ve container image rollout'unu birlikte yönetebilir; yanlış bir Wrangler config production Worker'ı değiştirebilir. Bu nedenle config tahmin edilmez, Cloudflare API'den okunan production metadata ile eşleştirilir.
