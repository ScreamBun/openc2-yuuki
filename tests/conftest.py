import time

import pytest


@pytest.fixture
def query_features():
    return {
        "headers": {
            "request_id": "abc123",
            "created": round(time.time() * 1000),
            "from": "Producer1"
        },
        "body": {
            "openc2": {
                "request": {
                    "action": "query",
                    "target": {
                        "features": [
                            "profiles"
                        ]
                    }
                }
            }
        }
    }


@pytest.fixture
def expected_response():
    return {
        'headers': {
            'request_id': 'abc123',
            'created': 1574571600000,
            'from': 'yuuki',
            'to': 'Producer1'
        },
        'body': {
            'openc2': {
                'response': {
                    'status': 200,
                    'status_text': 'OK - the Command has succeeded.',
                    'results': {
                        'profiles':
                            ['slpf',
                             'x-acme'
                             ]
                    }
                }
            }
        }
    }
