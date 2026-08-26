function isDriveAnswerKeyFile(file){return /__(CEVAP|CEVAP[_ -]?ANAHTARI|ANSWER[_ -]?KEY)\.pdf$/i.test(String(file?.name||''))}
