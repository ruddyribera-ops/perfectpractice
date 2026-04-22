import asyncio
import urllib.request
import json
import time

async def test():
    ts = int(time.time())
    req = urllib.request.Request(
        'http://localhost:8000/api/auth/register',
        data=json.dumps({'email': f'ltest_{ts}@test.com', 'password': 'Test1234!', 'name': 'L Test', 'role': 'student', 'grade': 1}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        token = json.loads(r.read().decode())['access_token']

    h = {'Authorization': f'Bearer {token}'}

    req2 = urllib.request.Request('http://localhost:8000/api/units/suma-y-resta', headers=h)
    with urllib.request.urlopen(req2, timeout=5) as r:
        unit = json.loads(r.read().decode())
        lessons = unit.get('lessons', [])
        print(f'Lessons in unit: {len(lessons)}')
        for l in lessons[:5]:
            print(f'  Lesson: id={l.get("id")}, title={l.get("title")}')

        if lessons:
            lid = lessons[0]['id']
            req3 = urllib.request.Request(f'http://localhost:8000/api/lessons/{lid}', headers=h)
            try:
                with urllib.request.urlopen(req3, timeout=5) as r:
                    lesson = json.loads(r.read().decode())
                    print(f'Lesson {lid}: {lesson.get("title")}, type={lesson.get("content_type")}')
            except urllib.error.HTTPError as e:
                print(f'Lesson {lid} ERROR: {e.code} - {e.read().decode()}')

asyncio.run(test())
