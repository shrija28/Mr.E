import urllib.request
import urllib.error
import json

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def main():
    creds = {'email': 'admin@smartkcet.com', 'password': 'admin@123'}
    
    print("--- 1. Admin login on Platform Admin endpoint ---")
    status, body = post('http://127.0.0.1:8000/api/auth/admin/login', creds)
    print(f"Status: {status}\nBody: {body}\n")
    
    print("--- 2. Admin login on Student endpoint ---")
    status, body = post('http://127.0.0.1:8000/api/auth/login', creds)
    print(f"Status: {status}\nBody: {body}\n")
    
    print("--- 3. Admin login on Institution endpoint ---")
    status, body = post('http://127.0.0.1:8000/api/auth/institution/login', creds)
    print(f"Status: {status}\nBody: {body}\n")

if __name__ == '__main__':
    main()
