# YILBAY Mikro-Hücresel Geliştirme Protokolü

Bu protokol proje için zorunlu geliştirme standardıdır.

## 1. Değişmez temel kural
**Her bağımsız kullanıcı işlevi / davranışı = ayrı geliştirme dosyası = ayrı mikro-hücre.**

Bir işlev değiştirildiğinde yalnızca o işlevin hücresi değiştirilir. İlgisiz bir işlevin kaynak dosyasına dokunulmaz. Yeni modül ilk günden mikro-hücrelere ayrılarak oluşturulur.

Örnekler:
- öğrenci ekleme ayrı hücre,
- öğrenci düzenleme ayrı hücre,
- öğrenci silme ayrı hücre,
- PDF büyütme ayrı hücre,
- PDF küçültme ayrı hücre,
- PDF döndürme ayrı hücre,
- ödev dosyası seçme ayrı hücre,
- AI ödev analizi ayrı hücre,
- öğretmen onayı ayrı hücre,
- tekrar sinyali ayrı hücre,
- YouTube arama ayrı hücre,
- OpenAI bağlantı testi ayrı hücre.

## 2. Mikro-hücre özellikleri
Her mikro-hücre:
- tek bir üst-seviye davranış/sorumluluk taşır,
- benzersiz dosya adına sahiptir,
- bağımlılıklarını ortak sözleşmeler üzerinden kullanır,
- tek başına sözdizimi testinden geçer,
- bundle oluşturma sırasında sabit sırada yüklenir,
- başka hücrenin iç uygulamasını kopyalamaz,
- başka hücreyi güncellemek zorunda bırakacak gizli yan etki oluşturmamalıdır.

## 3. Ortak çekirdek istisnası
Salt ortak altyapı tanımları (`core/store`, ortak UI yardımcıları, API istemci tabanı, tasarım tokenları) ortak çekirdek hücrelerinde tutulabilir. Ancak kullanıcıya ait ayrı eylemler ortak çekirdek içine gömülemez.

## 4. Geliştirme ve runtime ayrımı
`source/current/cells/micro/` gerçek JavaScript geliştirme kaynağıdır.

- `cells/micro/frontend/`: ön yüz mikro-hücreleri
- `cells/micro/backend/`: arka uç mikro-hücreleri
- `cells/micro-cell-manifest.json`: yükleme sırası ve hücre envanteri
- `cells/design-system/`: ortak saf görsel sistem

Dağıtılan:
- `app/public/app.js`
- `app/server.js`

dosyaları **elle düzenlenmez**. Bunlar mikro-hücrelerin manifest sırasıyla otomatik birleştirilmiş runtime bundle'larıdır.

## 5. Yeni modül protokolü
Yeni bir modül önce işlev envanterine ayrılır, sonra her işlev ayrı hücre olarak yazılır.

Örnek PDF modülü:
```
cells/micro/frontend/pdf/
  zoom-in.cell.js
  zoom-out.cell.js
  rotate-left.cell.js
  rotate-right.cell.js
  crop.cell.js
  next-page.cell.js
  previous-page.cell.js
  selection.cell.js
```

Tek bir `pdf.cell.js` içine bütün davranışların yazılması yasaktır.

## 6. Değişiklik izolasyonu
Bir güncellemede CI şunları zorunlu kontrol eder:
1. Değiştirilen mikro-hücrenin sözdizimi.
2. Tüm mikro-hücrelerin sözdizimi.
3. Her JS mikro-hücresinde tek üst-seviye davranış sözleşmesi.
4. Mikro-hücre manifest bütünlüğü.
5. Runtime bundle'ın yalnızca manifestten yeniden üretilmesi.
6. Tam uygulama statik testleri.
7. Gerçek `/health` smoke testi.
8. Kritik API endpoint smoke testleri.
9. Güvenlik kontrolleri.
10. SHA-256 paket doğrulaması.
11. Responsive UI sözleşmesi: farklı viewport genişlik/yüksekliklerinde ana içerik ve modal taşma koruması.
12. DPI/ölçek uyumluluğu: arayüz sabit fiziksel piksel varsayımı yapmamalıdır.

Bunlardan biri başarısızsa `release/latest.json` güncellenmez.

## 7. Yasaklar
- Yeni monolitik özellik dosyası oluşturmak yasaktır.
- Bir dosyada ilgisiz iki kullanıcı işlevi birleştirmek yasaktır.
- İlgisiz hücreyi aynı özellik değişikliğinde düzenlemek yasaktır.
- Hücreler arası iş mantığı kopyalamak yasaktır.
- Runtime bundle'ı doğrudan elle düzenlemek yasaktır.
- Test geçmeden release yayınlamak yasaktır.
- Ana yerleşimi yalnız sabit piksel genişlik/yükseklik varsayımına bağlamak yasaktır.
- Kullanıcının ekran çözünürlüğü veya Windows DPI ölçeklendirmesi nedeniyle erişilemeyen buton, modal veya ana içerik bırakmak yasaktır.

## 8. Ekran çözünürlüğü / DPI / viewport uyumluluk protokolü
YILBAY, çalıştırıldığı cihazın kullanılabilir ekran alanına otomatik uyum sağlamalıdır.

Zorunlu kurallar:
- Masaüstü arayüzü 1366×768, 1600×900, 1920×1080, 2560×1440 ve daha yüksek çözünürlüklerde kullanılabilir kalmalıdır.
- Windows %100, %125, %150 ve benzeri DPI ölçekleri tarayıcının CSS viewport ölçüleri üzerinden doğal olarak desteklenmelidir.
- Yerleşim ölçülerinde uygun yerlerde `clamp()`, `min()`, `max()`, `minmax()` ve akışkan grid kullanılmalıdır.
- Görünür alan yüksekliği için mümkün olduğunda dinamik viewport birimi (`dvh`) kullanılmalıdır.
- Düşük yükseklikte başlık, navigasyon, içerik padding'i ve kart boşlukları otomatik sıkılaşmalıdır.
- Dar genişlikte sidebar ve çok sütunlu gridler uygun kırılım noktalarında yeniden akmalıdır.
- Tablolar veri kaybetmeden kendi kapsayıcısı içinde yatay kayabilmelidir; tüm sayfanın kontrolsüz yatay taşması engellenmelidir.
- Modal pencereler viewport dışına taşmamalı; içerikleri kendi içinde kaydırılabilmelidir.
- Buton ve form alanları erişilebilir minimum tıklama alanını korumalıdır.
- Ekran boyutu çalışma sırasında değişirse (tam ekran, pencere boyutu, ekran taşıma, DPI değişimi) viewport profili yeniden hesaplanmalıdır.
- Viewport profilini hesaplamak ve resize olayını dinlemek ayrı mikro-hücreler olmalıdır.

## 9. Başlatma görünümü protokolü
Kalıcı `PROGRAMI_CALISTIR.bat` çalıştırıldığında:
- PowerShell/başlatıcı penceresi maksimize açılır.
- YILBAY uygulama penceresi tam ekran/maksimize açılır.
- Tam ekran açılış responsive tasarımın yerine geçmez; uygulama her çözünürlükte ayrıca uyumlu olmalıdır.
- PowerShell yalnız Node bootstrap'ı başlatmak için kullanılır; `ExecutionPolicy Bypass` veya PowerShell script tabanlı ana çalışma yolu kullanılmaz.

## 10. Sürüm politikası
- v0.8.0: modül-seviyesi hücresel mimari geçişi.
- **v0.8.1: her üst-seviye işlevi ayrı dosyaya ayıran mikro-hücre mimarisi.**
- v0.8.1 sonrasında bütün yeni geliştirmeler doğrudan mikro-hücre protokolüne göre yapılır.
- v0.9.5 ve sonrası: ekran çözünürlüğü/DPI/viewport uyumluluğu kalıcı UI sözleşmesidir.
