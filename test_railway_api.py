import json, sys
from urllib.request import Request, urlopen
from urllib.error import URLError

token = 'f2b0d590-65ba-4778-9664-66a35803ee77'
project_id = 'a8c01475-fd4c-4f2a-8512-2c0abd1dba0f'

url = f'https://backboard.railway.app/api/v1/projects/{project_id}/services'
req = Request(url, headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Python'})
try:
    resp = urlopen(req, timeout=15)
    data = json.loads(resp.read())
    print('Services:')
    for svc in data.get('services', []):
        name = svc.get('name', '?')
        status = svc.get('status', '?')
        created = str(svc.get('createdAt', ''))[:10]
        print(f'  {name} | status={status} | created={created}')
except URLError as e:
    print(f'HTTP Error: {e.code} {e.reason}')
    try:
        body = e.read().decode('utf-8', errors='replace')
        print(body[:500])
    except:
        pass
except Exception as e:
    print(f'Error: {e}')