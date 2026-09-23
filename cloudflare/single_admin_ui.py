from pathlib import Path

app_js=Path("/app/APP/frontend/dist/app-0.10.7.js")
online_js=Path("/app/APP/frontend/dist/genesis-online-01.js")

src=app_js.read_text(encoding="utf-8")
src=src.replace('${window.GENESIS_ROLE==="ADMIN"?`<hr><button data-act="institution"><span class="mi">＋</span>Yeni Kurum Oluştur</button><button data-act="institutions"><span class="mi">▣</span>Kurumları Yönet</button>${window.GENESIS_INSTITUTION_ID?`<button data-act="exit-institution"><span class="mi">↩</span>Yönetici Görünümüne Dön</button>`:""}`:""}',"")
src=src.replace(' if(a==="institution"){window.genesisCreateInstitution?.();return}\n if(a==="institutions"){window.genesisManageInstitutions?.();return}\n if(a==="exit-institution"){window.genesisExitInstitution?.();return}\n',"")
app_js.write_text(src,encoding="utf-8")

src=online_js.read_text(encoding="utf-8")
start=src.find('   if(window.GENESIS_ROLE==="ADMIN"){\n     menu.insertAdjacentHTML("beforeend",')
if start>=0:
    end=src.find("   }\n",start)
    if end<0:
        raise SystemExit("admin menu end not found")
    src=src[:start]+src[end+5:]
src=src.replace('''     if(window.GENESIS_ROLE==="ADMIN"){
       if(act==="create-institution")window.genesisCreateInstitution?.();
       if(act==="change-admin-password")window.genesisChangeAdminPassword?.();
     }
''',"",1)
online_js.write_text(src,encoding="utf-8")
