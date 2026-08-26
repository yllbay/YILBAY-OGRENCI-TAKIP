window.studentModal=()=>modal(`<h2>Yeni Öğrenci</h2><div class="formgrid">
<div class="field"><label>Ad Soyad</label><input id="sname"></div><div class="field"><label>Sınıf</label><input id="sgrade"></div>
<div class="field"><label>Hedef</label><input id="starget" value="YKS"></div>
<div class="field"><label>Kayıt Tarihi</label><input id="sregistered" type="date" value="${new Date().toISOString().slice(0,10)}"></div>
<div class="field"><label>Kurs Bitiş Tarihi</label><input id="senddate" type="date"></div>
<div class="field"><label>Haftalık Çalışma Günü</label><input id="sstudydays" type="number" min="1" max="7" value="6"></div>
<div class="field"><label>Günlük Çalışma Süresi (dk)</label><input id="sdailyminutes" type="number" min="30" max="600" step="15" value="120"></div>
<div class="field"><label>AI Dönem Planlama</label><select id="saiauto"><option value="true">Açık</option><option value="false">Kapalı</option></select></div>
</div>
<h3>Koçluk dersleri ve kaynak seviyesi</h3><div class="list">${courseLevelFields()}</div>
<div class="modal-actions"><button class="btn primary" onclick="addStudent()">Kaydet</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
