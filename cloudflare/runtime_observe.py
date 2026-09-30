import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.error

account=os.environ['CLOUDFLARE_ACCOUNT_ID'].strip()
token=os.environ['CLOUDFLARE_API_TOKEN']
now=int(time.time()*1000)
body={'queryId':'genesis-runtime-recovery', 'timeframe':{'from':now-15*60*1000,'to':now},
      'view':'events','limit':2000,'dry':True,'parameters':{'datasets':[], 'filters':[]}}
request=urllib.request.Request(f'https://api.cloudflare.com/client/v4/accounts/{account}/workers/observability/telemetry/query',
    data=json.dumps(body).encode(), headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(request,timeout=40) as response:
        result=json.load(response)
    Path('/tmp/observe/telemetry-'+str(now)+'.json').write_text(json.dumps(result,indent=2))
    print('OBSERVABILITY_QUERY_OK')
except urllib.error.HTTPError as error:
    detail=error.read().decode('utf-8','replace')
    Path('/tmp/observe/telemetry-error.txt').write_text(detail)
    print('OBSERVABILITY_HTTP',error.code)
