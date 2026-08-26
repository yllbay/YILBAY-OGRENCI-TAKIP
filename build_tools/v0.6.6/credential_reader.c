#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wincred.h>
#include <stdio.h>
#include <wchar.h>

static int ends_with_ci(const wchar_t *s, const wchar_t *suffix){
    size_t ls=wcslen(s), lx=wcslen(suffix);
    if(lx>ls) return 0;
    return _wcsicmp(s+ls-lx,suffix)==0;
}

int wmain(int argc, wchar_t **argv){
    const wchar_t *wanted = argc>1 ? argv[1] : L"YILBAY-OPENAI-API-HOME";
    const wchar_t *expectedUser = argc>2 ? argv[2] : L"YILBAY-DEVELOPMENT-HOME";
    DWORD count=0; PCREDENTIALW *creds=NULL;
    if(!CredEnumerateW(NULL,0,&count,&creds)) return 20;
    int rc=21;
    for(DWORD i=0;i<count;i++){
        PCREDENTIALW c=creds[i];
        if(!c || !c->TargetName) continue;
        if(_wcsicmp(c->TargetName,wanted)!=0 && !ends_with_ci(c->TargetName,wanted)) continue;
        if(expectedUser && *expectedUser){
            if(!c->UserName || _wcsicmp(c->UserName,expectedUser)!=0){ rc=22; continue; }
        }
        if(!c->CredentialBlob || c->CredentialBlobSize==0){ rc=23; continue; }
        DWORD chars=c->CredentialBlobSize/sizeof(wchar_t);
        fwrite(c->CredentialBlob,sizeof(wchar_t),chars,stdout);
        rc=0;
        break;
    }
    CredFree(creds);
    return rc;
}
