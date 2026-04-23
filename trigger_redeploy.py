"""Test Railway redeploy trigger via GitHub push"""
import subprocess, json

print('=== ATTEMPTING RAILWAY REDEPLOY VIA GITHUB ===')

# 1. Check git status and recent frontend changes
print('\n1. Git status:')
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout or 'No changes')

# 2. Check if Railway is watching the repo
print('\n2. Checking remote:')
result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
print(result.stdout)

# 3. Check last 5 commits
print('\n3. Recent commits:')
result = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True)
print(result.stdout)

# 4. Force-push frontend trigger by updating README with timestamp
import datetime
print('\n4. Creating trigger commit...')
try:
    with open('README.md', 'r') as f:
        readme = f.read()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = readme.split('\n')
    # Add deployment timestamp line
    lines = [l for l in lines if not l.startswith('<!-- DEPLOY')]
    lines.append(f'<!-- DEPLOY: {timestamp} -->')
    with open('README.md', 'w') as f:
        f.write('\n'.join(lines))
    print(f'   Updated README.md with timestamp: {timestamp}')
except Exception as e:
    print(f'   ERROR: {e}')

print('\n5. Git diff for README:')
result = subprocess.run(['git', 'diff', 'README.md'], capture_output=True, text=True)
print(result.stdout[:300] if result.stdout else 'No changes')

# 6. Check Railway.toml for frontend service
print('\n6. Checking for Railway.toml in repo:')
import os
for f in ['railway.toml', 'frontend/railway.toml', 'backend/railway.toml']:
    exists = os.path.isfile(f)
    label = 'EXISTS' if exists else 'MISSING'
    print(f'   {label}: {f}')