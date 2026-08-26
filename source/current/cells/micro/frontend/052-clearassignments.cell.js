window.clearAssignments=()=>{if(!db.assignments.length||!confirm('Atamalar ekranındaki TÜM kayıtlar silinsin mi? Akademik sonuçlar ve AI analiz geçmişi korunur.'))return;db.assignments=[];save();assignments()}

