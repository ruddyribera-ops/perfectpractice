import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# Test the three working frontend URLs - check what they serve
urls = [
    'https://math-platform-frontend.railway.app/',
    'https://perfectpractice-frontend.railway.app/',
    'https://mathplatform.railway.app/',
]

for url in urls:
    print(f'\n=== {url} ===')
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req, timeout=10)
        print(f'Status: {resp.status}')
        print(f'Headers: server={resp.headers.get("server","?")}, content-type={resp.headers.get("content-type","?")}')
        body = resp.read()[:500].decode('utf-8', errors='replace')
        print(f'Body preview: {body[:300]}')
    except URLError as e:
        print(f'HTTP {e.code}: {e.reason}')
    except Exception as e:
        print(f'Error: {e}')

# Try login page specifically
print('\n=== LOGIN PAGE ===')
for url in urls:
    login_url = url.rstrip('/') + '/login'
    try:
        req = Request(login_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req, timeout=10)
        print(f'{login_url}: {resp.status}')
        body = resp.read()[:200].decode('utf-8', errors='replace')
        print(f'  Preview: {body[:150]}')
    except Exception as e:
        print(f'{login_url}: {e}')

# Try topics page
print('\n=== TOPICS PAGE ===')
for url in urls:
    topics_url = url.rstrip('/') + '/topics'
    try:
        req = Request(topics_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req, timeout=10)
        print(f'{topics_url}: {resp.status}')
    except Exception as e:
        print(f'{topics_url}: {e}')