import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# Test more URL patterns for Railway frontend
base_urls = [
    'https://math-platform-frontend.railway.app',
    'https://perfectpractice-frontend.railway.app',
    'https://mathplatform.railway.app',
    'https://perfectpractice.up.railway.app',
    'https://math-platform.up.railway.app',
]

# Also test different paths on known backend URL
paths = ['/', '/health', '/api/health']
for url in base_urls:
    for path in paths:
        full_url = url + path
        try:
            req = Request(full_url, headers={'User-Agent': 'Python'})
            resp = urlopen(req, timeout=6)
            body = resp.read()[:200]
            print(f'OK {resp.status}: {full_url}')
        except URLError as e:
            print(f'FAIL {e.code}: {full_url}')
        except Exception as e:
            print(f'ERR: {full_url} -> {e}')

# Test GitHub raw content for railway.toml to understand config
gh_url = 'https://raw.githubusercontent.com/ruddyribera-ops/perfectpractice/main/frontend/Dockerfile'
req = Request(gh_url, headers={'User-Agent': 'Python'})
try:
    resp = urlopen(req, timeout=10)
    print(f'\nGitHub raw Dockerfile: {resp.status}')
    print(resp.read()[:300].decode())
except Exception as e:
    print(f'GitHub raw: {e}')