window.assignmentModal=()=>{modal(`<h2>Yeni Atama</h2><div class="formgrid">
<div class="field"><label>Öğrenci</label><select id="astudent">${db.students.map(s=>`<option value="${s.id}">${s.name}</option>`).join("")}</select></div>
<div class="field"><label>Atama türü</label><select id="akind" onchange="refreshAssignmentItems()"><option>PDF Kaynak</option><option>Online Sınav</option></select></div>
<div class="field" style="grid-column:1/-1"><label>İçerik</label><select id="aitem"></select></div>
</div><div class="modal-actions"><button class="btn primary" onclick="addAssignment()">Ata</button> <button class="btn ghost" onclick="closeModal()">İptal</button></div>`);refreshAssignmentItems()}
