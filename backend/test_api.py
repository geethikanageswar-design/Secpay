import urllib.request
import json
import traceback

def test_api():
    try:
        req = urllib.request.Request(
            'http://localhost:8000/api/payments/create-order',
            data=json.dumps({'bill_id': 5}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        res = urllib.request.urlopen(req)
        print("Response:", res.read())
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        print("Response Body:", e.read().decode('utf-8'))
    except Exception as e:
        print("Other exception:")
        traceback.print_exc()

if __name__ == '__main__':
    test_api()
