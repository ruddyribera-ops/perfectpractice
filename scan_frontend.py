import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# The three URLs we found all serve Railway's placeholder ASCII art
# Our Next.js app is NOT deployed yet. Let's test more patterns
patterns = [
    'https://enchanting-possibility.railway.app',
    'https://enchanting-possibility-2.railway.app',
    'https://mathplatform-perfectpractice.railway.app',
    'https://perfectpractice-app.railway.app',
    'https://perfectpractice-web.railway.app',
    'https://mathplatform-app.railway.app',
    'https://math-platform-app.railway.app',
    'https://math-platform-web.railway.app',
    'https://math-platform-math-platform.railway.app',
    'https://perfectpractice-frontend.railway.app',
    'https://math-platform-frontend.railway.app',
    'https://mathplatform.railway.app',
]

# Also try to get project services from Railway API with correct endpoint
print('=== TESTING RAILWAY API ===')
token = 'f2b0d590-65ba-4778-9664-66a35803ee77'
railway_endpoints = [
    'https://backboard.railway.app/api/v1/me',
    'https://backboard.railway.app/api/v1/account',
    'https://backboard.railway.app/api/v2/users/me',
    'https://backboard.railway.app/api/v1/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f/services',
    'https://railway.app/api/v1/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f',
]
for url in railway_endpoints:
    try:
        req = Request(url, headers={'Authorization': f'Bearer {token}', 'User-Agent': 'curl/7.68.0'})
        resp = urlopen(req, timeout=8)
        data = json.loads(resp.read())
        print(f'OK {url}: {str(data)[:200]}')
    except URLError as e:
        print(f'FAIL {url}: {e.code} {e.reason}')
    except Exception as e:
        print(f'ERR {url}: {e}')

print('\n=== SCANNING FRONTEND URLS ===')
for url in patterns:
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req, timeout=5)
        body = resp.read()
        size = len(body)
        is_placeholder = b'Railway API' in body
        print(f'{"PLACEHOLDER" if is_placeholder else "APP"} {resp.status} {url} ({size} bytes)')
    except URLError as e:
        print(f'404 {url}: {e.code}')
    except Exception as e:
        print(f'ERR {url}: {e}')