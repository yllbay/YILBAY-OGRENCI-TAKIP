# YILBAY Hücresel Geliştirme Protokolü

Bu protokol proje için zorunlu geliştirme standardıdır.

## 1. Temel kural
Her bağımsız davranış veya işlev kendi geliştirme hücresinde tutulur. Bir değişiklik yalnızca ilgili hücrede yapılır. Başka hücreler, değişiklik için zorunlu bir arayüz sözleşmesi değişmediği sürece düzenlenmez.

## 2. Hücre özellikleri
Her hücre:
- tek sorumluluk taşır,
- benzersiz bir hücre kimliğine sahiptir,
- bağımlılıklarını manifestte açıklar,
- kendi sözdizimi/statik testinden geçer,
- tam uygulama smoke testinden bağımsız olarak da doğrulanabilir,
- başka hücrenin iç durumuna gizli şekilde bağlanamaz.

## 3. Geliştirme ve runtime ayrımı
`source/current/cells/` gerçek geliştirme kaynağıdır.

Dağıtılan `app/public/app.js` ve `app/server.js`, hücrelerin sabit sırada otomatik birleştirilmiş runtime bundle'larıdır. Runtime bundle doğrudan elle düzenlenmez.

Bir özellik değiştirildiğinde yalnızca ilgili hücre düzenlenir; CI hücrelerden bundle üretir, test eder ve paketler.

## 4. Hücre sınıfları
- `frontend/core`: veri deposu, ortak UI, bootstrap
- `frontend/pages`: ekranlar
- `frontend/features`: buton/işlem davranışları
- `frontend/services`: API istemcileri
- `backend/core`: HTTP/runtime
- `backend/services`: OpenAI, maliyet, planlayıcı, homework vision, YouTube
- `backend/routes`: endpoint yönlendirme
- `design-system`: ortak font, renk, spacing, button/table/form standartları

## 5. Yeni özellik protokolü
Yeni modül doğrudan monolitik dosyaya eklenmez.

Örnek:
- PDF küçültme: `cells/frontend/features/pdf/zoom-out.cell.js`
- PDF büyütme: `cells/frontend/features/pdf/zoom-in.cell.js`
- PDF sayfa döndürme: `cells/frontend/features/pdf/rotate.cell.js`

Her yeni özellik kendi hücresi + manifest kaydı + hücre testi ile oluşturulur.

## 6. Değişiklik izolasyonu
Bir hücre değiştirildiğinde CI şunları zorunlu kontrol eder:
1. Hücre sözdizimi.
2. Hücre manifest bütünlüğü.
3. Bundle yeniden üretimi.
4. Tam uygulama statik testleri.
5. Gerçek `/health` smoke testi.
6. Güvenlik kontrolleri.
7. SHA-256 paket doğrulaması.

Bu kontroller geçmeden `release/latest.json` güncellenmez.

## 7. Yasaklar
- Yeni büyük monolitik dosya oluşturmak yasaktır.
- İlgisiz hücreyi aynı özellik değişikliğinde düzenlemek yasaktır.
- Hücreler arası kopyala-yapıştır iş mantığı yasaktır.
- Runtime bundle'ı elle düzenlemek yasaktır.
- Test geçmeden release yayınlamak yasaktır.

## 8. Sürüm politikası
Hücresel mimariye geçiş sürümü: `v0.8.0`.
Bundan sonraki bütün geliştirmeler bu protokole göre yapılacaktır.
