import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# Try Railway API with different endpoints
token = 'f2b0d590-65ba-4778-9664-66a35803ee77'

endpoints = [
    ('GET', 'https://backboard.railway.app/api/v1/me', None),
    ('GET', 'https://backboard.railway.app/api/v1/projects', None),
    ('GET', 'https://backboard.railway.app/api/v1/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f', None),
    ('GET', 'https://backboard.railway.app/api/v2/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f', None),
]

for method, url, data in endpoints:
    req = Request(url, headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Python'})
    try:
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read())
        print(f'{url}: {resp.status} -> {str(result)[:200]}')
    except URLError as e:
        print(f'{url}: {e.code} {e.reason}')
    except Exception as e:
        print(f'{url}: ERROR {e}')