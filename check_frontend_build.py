"""Build frontend and show exactly what Railway will deploy"""
import subprocess, sys

print('=== FRONTEND BUILD TEST ===')

# 1. Check tsconfig paths
print('\n1. Checking tsconfig paths...')
try:
    with open('frontend/tsconfig.json') as f:
        import json
        tc = json.load(f)
        paths = tc.get('compilerOptions', {}).get('paths', {})
        baseUrl = tc.get('compilerOptions', {}).get('baseUrl', '')
        print(f'   baseUrl: {baseUrl}')
        print(f'   paths: {json.dumps(paths, indent=2)}')
except Exception as e:
    print(f'   ERROR: {e}')

# 2. Check if @/* resolves to ./app/*
print('\n2. Checking app directory structure...')
import os, glob
app_dir = 'frontend/app'
if os.path.isdir(app_dir):
    print(f'   frontend/app/ EXISTS')
    files = []
    for root, dirs, filenames in os.walk(app_dir):
        for f in filenames:
            files.append(os.path.join(root, f))
    print(f'   Files in frontend/app/: {len(files)}')
    print(f'   First 10: {[f.replace("frontend/app/","") for f in files[:10]]}')
else:
    print(f'   frontend/app/ DOES NOT EXIST!')

# 3. Check for duplicate/ghost directories
print('\n3. Checking for ghost directories...')
for d in ['frontend/components/components', 'frontend/lib/lib', 'frontend/hooks/hooks',
          'frontend/contexts/contexts', 'frontend/app/components/components']:
    if os.path.isdir(d):
        print(f'   GHOST FOUND: {d}/')
    else:
        print(f'   OK: {d}/ does not exist')

# 4. Check next.config.js
print('\n4. Next.js config...')
try:
    with open('frontend/next.config.js') as f:
        print(f'   {f.read().strip()}')
except Exception as e:
    print(f'   ERROR: {e}')

# 5. Check for standalone output
print('\n5. Checking .next/standalone exists...')
if os.path.isdir('frontend/.next/standalone'):
    print('   YES - standalone build exists')
else:
    print('   NO - standalone build missing (need to run `npm run build`)')

# 6. List key frontend files
print('\n6. Key frontend files:')
key_files = [
    'frontend/package.json',
    'frontend/Dockerfile',
    'frontend/tsconfig.json',
    'frontend/app/page.tsx',
    'frontend/app/providers.tsx',
    'frontend/app/topics/page.tsx',
]
for f in key_files:
    status = 'EXISTS' if os.path.isfile(f) else 'MISSING'
    print(f'   {status}: {f}')