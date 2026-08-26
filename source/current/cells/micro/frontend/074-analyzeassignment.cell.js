window.analyzeAssignment=id=>{
 const a=db.assignments.find(x=>x.id===id);if(!a)return;const rc=assignmentResourceContext(a);
 modal(`<h2>AI ile Ödev Analizi</h2><p><b>${a.title}</b><br>${studentName(a.studentId)} · ${a.course} / ${a.topic}</p>
 <div class="field"><label>Öğrencinin tamamladığı PDF veya görsel</label><input id="homeworkFile" type="file" accept=".pdf,image/png,image/jpeg,image/webp"></div>
 <div class="field"><label>Cevap anahtarı (opsiyonel)</label><textarea id="answerKey" rows="4" placeholder="Örn: 1-A, 2-C, 3-B..."></textarea></div>
 <div class="notice"><div><b>Kaynak bağlantısı</b>${rc?.driveFileId?`Drive kaynak PDF bağlı${rc.answerKeyDriveFileId?" · Cevap anahtarı bağlı":""}${rc.questionCount?` · ${rc.questionCount} soru`:""}`:"Drive kaynak PDF bağlı değil"}</div></div>
 <div class="notice"><div><b>Analiz kapsamı</b>AI; doğru, yanlış ve boşları; görülebilen çözüm yollarını; hata türlerini ve başarı yüzdesini çıkarır. Cevap anahtarı verilirse doğruluk yükselir.</div></div>
 <div class="modal-actions"><button class="btn primary" onclick="submitHomeworkAnalysis(${id})">Dosyayı Tara</button><button class="btn ghost" onclick="closeModal()">İptal</button></div>`)
}
