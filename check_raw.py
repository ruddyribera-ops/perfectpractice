import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# Get raw bytes and check encoding
for url in ['https://math-platform-frontend.railway.app/', 'https://perfectpractice-frontend.railway.app/']:
    print(f'\n=== {url} ===')
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req, timeout=10)
        body = resp.read()
        print(f'Status: {resp.status}, Size: {len(body)}, Type: {resp.headers.get("content-type","?")}')
        print(f'Raw bytes: {body[:200]}')
        try:
            print(f'UTF-8: {body.decode("utf-8")[:300]}')
        except:
            try:
                print(f'Latin-1: {body.decode("latin-1")[:300]}')
            except Exception as ex:
                print(f'Decode error: {ex}')
    except Exception as e:
        print(f'Error: {e}')