import json

import requests

import openc2_command


headers = {"Content-Type": "application/openc2-cmd+json;version=1.0"}

response = requests.post("http://127.0.0.1:9001", json=openc2_command.query_features, headers=headers, verify=False)

print(json.dumps(response.json(), indent=4))
