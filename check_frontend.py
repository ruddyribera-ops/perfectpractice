import json, re
from urllib.request import Request, urlopen
from urllib.error import URLError

# Check which URL serves our Next.js app by looking for Math Platform content
test_urls = [
    'https://math-platform-frontend.railway.app/',
    'https://perfectpractice-frontend.railway.app/',
    'https://mathplatform.railway.app/',
]

for url in test_urls:
    print(f'\n=== CHECKING: {url} ===')
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req, timeout=10)
        body_bytes = resp.read()
        content_type = resp.headers.get('content-type', '')
        print(f'Status: {resp.status}, Content-Type: {content_type}')
        print(f'Content-Length: {len(body_bytes)}')

        # Decode carefully
        for enc in ['utf-8', 'latin-1']:
            try:
                body = body_bytes.decode(enc)
                print(f'Decoded ({enc}): {body[:400]}')
                break
            except:
                pass

        # Look for Next.js specific markers
        if b'__NEXT_DATA__' in body_bytes:
            print('  -> Has __NEXT_DATA__ (Next.js!)')
        if b'next' in body_bytes.lower():
            print('  -> References "next"')
        if b'Math Platform' in body_bytes or b'math-platform' in body_bytes:
            print('  -> Has Math Platform branding!')
        if b'<!DOCTYPE html>' in body_bytes or b'<!doctype html>' in body_bytes:
            print('  -> Is HTML document')

    except URLError as e:
        print(f'HTTP {e.code}: {e.reason}')
    except Exception as e:
        print(f'Error: {e}')