#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wincred.h>
#include <string>
#include <iostream>
#include <vector>
#include <algorithm>

static std::string jsonEscape(const std::string& s){
  std::string o; o.reserve(s.size()+16);
  for(unsigned char c: s){
    switch(c){
      case '\\': o += "\\\\"; break; case '"': o += "\\\""; break;
      case '\n': o += "\\n"; break; case '\r': o += "\\r"; break; case '\t': o += "\\t"; break;
      default: if(c>=0x20) o.push_back((char)c);
    }
  }
  return o;
}
static std::string wideToUtf8(const std::wstring& w){
  if(w.empty()) return {};
  int n=WideCharToMultiByte(CP_UTF8,0,w.data(),(int)w.size(),nullptr,0,nullptr,nullptr);
  std::string s(n,'\0');
  WideCharToMultiByte(CP_UTF8,0,w.data(),(int)w.size(),s.data(),n,nullptr,nullptr);
  return s;
}
static bool endsWithI(const std::wstring& value,const std::wstring& suffix){
  if(value.size()<suffix.size()) return false;
  return _wcsicmp(value.c_str()+value.size()-suffix.size(),suffix.c_str())==0;
}
static std::string blobToUtf8(const BYTE* p,DWORD n){
  if(!p || n==0) return {};
  if(n>=2 && (n%2)==0){
    const wchar_t* w=(const wchar_t*)p; size_t count=n/2;
    while(count && w[count-1]==L'\0') --count;
    bool plausible=true;
    for(size_t i=0;i<count;i++){ if(w[i]==0){ plausible=false; break; } }
    if(plausible){ auto s=wideToUtf8(std::wstring(w,w+count)); if(!s.empty()) return s; }
  }
  std::string s((const char*)p,(const char*)p+n);
  while(!s.empty() && s.back()=='\0') s.pop_back();
  return s;
}
int wmain(int argc,wchar_t** argv){
  const std::wstring wanted = argc>1 ? argv[1] : L"YILBAY-OPENAI-API-HOME";
  const std::wstring expectedUser = argc>2 ? argv[2] : L"YILBAY-DEVELOPMENT-HOME";
  DWORD count=0; PCREDENTIALW* creds=nullptr;
  if(!CredEnumerateW(nullptr,0,&count,&creds)){
    DWORD e=GetLastError();
    std::cout << "{\"ok\":false,\"matched\":false,\"win32\":" << e << "}";
    return 0;
  }
  bool targetMatched=false, userMatched=false;
  for(DWORD i=0;i<count;i++){
    PCREDENTIALW c=creds[i]; if(!c || !c->TargetName) continue;
    std::wstring target(c->TargetName);
    if(!endsWithI(target,wanted)) continue;
    targetMatched=true;
    std::wstring user=c->UserName?std::wstring(c->UserName):L"";
    bool um=expectedUser.empty() || _wcsicmp(user.c_str(),expectedUser.c_str())==0;
    userMatched=um;
    if(!um) continue;
    std::string secret=blobToUtf8(c->CredentialBlob,c->CredentialBlobSize);
    std::cout << "{\"ok\":true,\"matched\":true,\"targetMatched\":true,\"userMatched\":true,\"target\":\""
      << jsonEscape(wideToUtf8(target)) << "\",\"username\":\"" << jsonEscape(wideToUtf8(user))
      << "\",\"secret\":\"" << jsonEscape(secret) << "\",\"type\":" << c->Type
      << ",\"persist\":" << c->Persist << ",\"blobSize\":" << c->CredentialBlobSize << "}";
    CredFree(creds); return 0;
  }
  std::cout << "{\"ok\":true,\"matched\":false,\"targetMatched\":" << (targetMatched?"true":"false")
            << ",\"userMatched\":" << (userMatched?"true":"false") << ",\"count\":" << count << "}";
  CredFree(creds); return 0;
}
