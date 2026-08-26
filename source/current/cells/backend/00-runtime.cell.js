/* CELL:00-runtime | layer:backend | generated-from:v0.7.2 */
const http=require("http"),fs=require("fs"),path=require("path"),cp=require("child_process");
const port=Number(process.env.PORT||43127), pub=path.join(__dirname,"public");
const root=path.resolve(__dirname,"..");
const runtime=path.join(root,"runtime");
const secretFile=path.join(runtime,"api_secrets.json");
const usageFile=path.join(runtime,"ai_usage.jsonl");
fs.mkdirSync(runtime,{recursive:true});

/* CELL:10-secrets-integrations | layer:backend | generated-from:v0.7.2 */
