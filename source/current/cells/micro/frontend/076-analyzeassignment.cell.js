window.analyzeAssignment=id=>{
 const a=db.assignments.find(x=>x.id===id);if(!a)return;const rc=assignmentResourceContext(a);
 modal(`<h2>AI ile Ödev Analizi</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} · ${a.course} / ${a.topic}</p>
 <div class="field"><label>Ödev dosyası kaynağı</label><select id="homeworkSource" onchange="toggleHomeworkSource()"><option value="local">Bu bilgisayardan</option><option value="drive">Google Drive</option></select></div>
 <div id="homeworkLocalWrap" class="field"><label>Öğrencinin tamamladığı PDF veya görsel</label><input id="homeworkFile" type="file" accept=".pdf,image/png,image/jpeg,image/webp"></div>
 <div id="homeworkDriveWrap" class="field" style="display:none"><label>Drive dosya bağlantısı veya kimliği</label><input id="homeworkDriveInput" placeholder="https://drive.google.com/file/d/... veya dosya kimliği"></div>
 <div class="field"><label>Cevap anahtarı (opsiyonel)</label><textarea id="answerKey" rows="4" placeholder="Örn: 1-A, 2-C, 3-B..."></textarea></div>
 <div class="notice"><div><b>Doğrudan Luna Vision</b>Seçtiğiniz öğrenci PDF/görseli doğrudan Luna’ya gönderilir. Bilgisayardan yüklemede Drive kontrol edilmez.</div></div>
 <div class="notice"><div><b>Analiz kapsamı</b>AI; doğru, yanlış ve boşları belirler. Ayrıca öğrencinin el yazısı çözüm adımlarını, kullandığı yöntemi, ilk hata adımını, kavramsal/işlemsel/dikkat hatalarını, gereksiz veya eksik adımları ve daha uygun çözüm yaklaşımını soru bazında değerlendirir.</div></div>
 <div class="modal-actions"><button class="btn primary" onclick="submitHomeworkAnalysis(${id})">Dosyayı Tara</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
}
