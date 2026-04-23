import json
from urllib.request import Request, urlopen
from urllib.error import URLError

# All URLs returned Railway placeholder (336 bytes, "Home of the Railway API")
# Our Next.js app is NOT deployed. Let's check what Railway shows in dashboard

# Try Railway's own API to get deployment status
token = 'f2b0d590-65ba-4778-9664-66a35803ee77'

# Railway docs suggest these endpoints - let's try
print('=== RAILWAY API ENDPOINTS ===')
endpoints = [
    'https://railway.app/api/users/me',
    'https://railway.app/api/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f',
    'https://backboard.railway.app/api/v1/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f',
    'https://backboard.railway.app/api/v2/projects/a8c01475-fd4c-4f2a-8512-2c0abd1dba0f/deployments',
]
for url in endpoints:
    try:
        req = Request(url, headers={
            'Authorization': f'Bearer {token}',
            'User-Agent': 'curl/7.68.0',
            'Content-Type': 'application/json'
        })
        resp = urlopen(req, timeout=8)
        data = json.loads(resp.read())
        print(f'OK {url}: {str(data)[:300]}')
    except URLError as e:
        err_body = ''
        try:
            err_body = e.read().decode()
        except:
            pass
        print(f'FAIL {url}: {e.code} {e.reason} {err_body[:100]}')
    except Exception as e:
        print(f'ERR {url}: {e}')

# Let's also try GitHub API to check repo and workflows
print('\n=== GITHUB REPO STATUS ===')
try:
    # Get repo info
    req = Request('https://api.github.com/repos/ruddyribera-ops/perfectpractice',
                  headers={'User-Agent': 'Mozilla/5.0'})
    resp = urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f'Repo: {data.get("full_name")} | pushes: {data.get("pushed_at")} | size: {data.get("size")}KB')
    print(f'Default branch: {data.get("default_branch")}')
except Exception as e:
    print(f'GitHub repo: {e}')

# Check Actions
try:
    req = Request('https://api.github.com/repos/ruddyribera-ops/perfectpractice/actions/runs',
                  headers={'User-Agent': 'Mozilla/5.0'})
    resp = urlopen(req, timeout=10)
    data = json.loads(resp.read())
    runs = data.get('workflow_runs', [])
    print(f'\nRecent Actions runs ({len(runs)}):')
    for run in runs[:5]:
        print(f"  {run.get('name','?')} | {run.get('status','?')} | {run.get('conclusion','?')} | {run.get('created_at','?')[:10]}")
except Exception as e:
    print(f'GitHub Actions: {e}')