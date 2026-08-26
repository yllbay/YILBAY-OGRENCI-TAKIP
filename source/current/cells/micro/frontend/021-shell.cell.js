function shell(content,active=view){app().innerHTML=`<div class="top"><div class="brand-wrap"><div class="brandmark">Y</div><div><div class="brand">YILBAY Öğrenci Takip</div><div class="brand-sub">Akademik Koçluk Yönetim Sistemi</div></div></div><div class="top-right"><span class="version">v0.9.6</span></div></div><div class="layout"><aside>
<div class="nav-section">Yönetim</div>${nav("dashboard","Genel Bakış",active)}${nav("students","Öğrenciler",active)}${nav("profile","Öğrenci Profili",active)}
<div class="nav-section">Akademik İçerik</div>${nav("curriculum","Ders ve Üniteler",active)}${nav("resources","Kaynak Havuzu",active)}${nav("exams","Online Sınavlar",active)}
<div class="nav-section">Operasyon</div>${nav("assignments","Atamalar",active)}${nav("results","Başarı Sonuçları",active)}${nav("program","Haftalık Program",active)}
<div class="nav-section">Sistem</div>${nav("integrations","AI ve API Entegrasyonları",active)}
</aside><main><div class="page">${content}</div></main></div>`}


