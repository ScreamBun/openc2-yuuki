import requests
import json

query_features = {
        "action": "query",
        "target": {
            "features": ["versions","profiles"]
        },
        "args": {
            "response_requested": "complete"
        }
    }

as_json = json.dumps(query_features)
my_byte_header = bytearray.fromhex('9001')
as_json = my_byte_header.hex() + as_json
headers = {"Content-Type" : "application/openc2-cmd+json;version=1.0"}

response = requests.post("http://127.0.0.1:9001", data=as_json, headers=headers, verify=False)

print('Sent OpenC2 Command')
print(json.dumps(response.json(), indent=4))
pass