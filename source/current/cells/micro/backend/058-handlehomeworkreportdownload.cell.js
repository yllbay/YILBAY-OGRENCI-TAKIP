function handleHomeworkReportDownload(u,res){const m=String(u.pathname||'').match(/^\/api\/reports\/homework-pdf\/([0-9]+_[a-f0-9]{1,16})$/i);if(!m){res.writeHead(404);return res.end('Not found')}const f=path.join(runtime,'homework_reports',m[1]+'.pdf');if(!fs.existsSync(f)){res.writeHead(404);return res.end('Not found')}const d=fs.readFileSync(f);res.writeHead(200,{'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="YILBAY_Odev_Analiz_Karnesi.pdf"','Content-Length':d.length,'Cache-Control':'no-store'});return res.end(d)}

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */

/* CELL:60-youtube | layer:backend | generated-from:v0.7.2 */
