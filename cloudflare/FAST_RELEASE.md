# Fast Cloudflare Release Bridge

Bu dal yalnızca GENESIS paketini Cloudflare'a taşımak için kullanılır.

## Tasarım

- Geliştirme burada yapılmaz.
- Her yayın için yalnız `cloudflare/package/` altında tek deploy paketi güncellenir.
- Paket commit'i otomatik olarak yalnız bir workflow çalıştırır.
- Workflow cache veya uzun süreli artifact üretmez.
- `fetch-depth: 1` ile yalnız gerekli commit çekilir.
- Aynı anda ikinci deploy başlarsa eski çalışma iptal edilir.
- Public repository üzerindeki standart `ubuntu-latest` runner kullanılır.
- Cloudflare'a resmi `cloudflare/wrangler-action@v4` ile deploy edilir.

## Gerekli repository secrets

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Token veya Account ID hiçbir zaman paket dosyasına yazılmamalıdır.

## Paket yapısı

```
cloudflare/package/
  wrangler.jsonc   veya wrangler.toml
  Dockerfile       gerekiyorsa
  Worker/container kaynakları
  verify.sh        opsiyonel hızlı doğrulama
```

Canlı Worker'ın gerçek Wrangler/Container ayarları Cloudflare inventory ile doğrulandıktan sonra bu klasör doldurulur.
