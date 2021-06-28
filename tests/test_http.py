import json
import subprocess
import time

import pytest
import cbor2
import requests


@pytest.fixture(scope="module", autouse=True)
def start_yuuki(request):
    proc = subprocess.Popen(["python", "yuuki/tests/http_example.py"])
    time.sleep(3)
    request.addfinalizer(proc.kill)


@pytest.mark.parametrize("data_format, encode, decode", [
    ("json", json.dumps, json.loads),
    ("cbor", cbor2.dumps, cbor2.loads)
])
class TestHTTP:
    def test_query(self, data_format, encode, decode, query_features, expected_response):
        headers = {"Content-Type": f"application/openc2-cmd+{data_format};version=1.0",
                   "Accept": f"application/openc2-rsp+{data_format};version=1.0"}
        response = requests.post("http://127.0.0.1:9001", data=encode(query_features), headers=headers, verify=False)
        expected_response['headers'].pop('created')
        actual_response = decode(response.content)
        actual_response['headers'].pop('created')

        assert expected_response == actual_response
