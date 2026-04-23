"""Test Railway backend API endpoints"""
import json, sys
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE = "https://perfectpractice-production.up.railway.app"

def get(path, token=None):
    try:
        headers = {"User-Agent": "Python"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(BASE + path, headers=headers)
        resp = urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read())
    except URLError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

def post(path, data):
    try:
        body = json.dumps(data).encode()
        req = Request(BASE + path, data=body,
                     headers={"Content-Type": "application/json", "User-Agent": "Python"})
        resp = urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read())
    except URLError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

print("=== BACKEND HEALTH ===")
s, b = get("/api/health")
print(f"Health: {s} -> {b}")

print("\n=== AUTH ===")
s, b = post("/api/auth/login", {"email":"student@test.com","password":"test123"})
print(f"Login: {s} -> token={bool(b.get('access_token')) if isinstance(b,dict) else b}")
token = b.get("access_token","") if isinstance(b,dict) else ""

print("\n=== CURRICULUM ===")
s, b = get("/api/topics")
print(f"Topics (no auth): {s} -> {len(b) if isinstance(b,list) else b}")
s, b = get("/api/topics", token=token)
print(f"Topics (auth): {s} -> {len(b) if isinstance(b,list) else b}")

if isinstance(b, list) and b:
    slug = b[0]["slug"]
    s, detail = get(f"/api/topics/{slug}")
    print(f"Topic detail ({slug}): {s} -> {len(detail.get('units',[]))} units, desc={detail.get('description','')[:50] if isinstance(detail,dict) else '?'}")

print("\n=== UNITS ===")
s, b = get("/api/units")
print(f"Units (no auth): {s} -> {b if isinstance(b,str) else len(b) if isinstance(b,list) else b}")

print("\n=== LOGIN FLOWS ===")
for email in ["student@test.com","profesor@test.com","padre@test.com"]:
    s, b = post("/api/auth/login", {"email":email,"password":"test123"})
    print(f"Login {email}: {s} -> {'OK' if b.get('access_token') else 'FAIL'}")

print("\nDONE")