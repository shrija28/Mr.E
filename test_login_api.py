import urllib.request
import json

url = 'http://127.0.0.1:8000/api/auth/admin/login'
data = json.dumps({'email': 'admin@smartkcet.com', 'password': 'admin@123'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.getcode()}")
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Error Code: {e.code}")
    print(e.read().decode('utf-8'))
