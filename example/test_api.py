"""测试 store API"""
import django, os, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
import json

User = get_user_model()
print(f"Users count: {User.objects.count()}")
for u in User.objects.all():
    print(f"  User: {u.username}, superuser={u.is_superuser}")

# Try login with Client
c = Client()
resp = c.post('/admin/api/rbac/login/', json.dumps({'username': 'admin', 'password': 'admin'}),
              content_type='application/json')
print(f"Login admin/admin: {resp.status_code} {resp.json()}")

# If that doesn't work, try direct
if resp.status_code != 200:
    resp2 = c.post('/admin/login/', {'username': 'admin', 'password': 'admin', 'csrfmiddlewaretoken': ''})
    print(f"Django login: {resp2.status_code}")

# Test categories API
resp3 = c.get('/admin/api/store/categories/')
print(f"Categories API: {resp3.status_code}")
if resp3.status_code == 200:
    data = resp3.json()
    print(f"  data: {json.dumps(data, ensure_ascii=False)[:300]}")
else:
    print(f"  body: {resp3.content[:200].decode('utf-8', errors='replace')}")
