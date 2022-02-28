import time
import uuid

query_features = {
    "headers": {
        "request_id": str(uuid.uuid4()),
        "created": round(time.time() * 1000),
        "from": "Producer1"
    },
    "body": {
        "openc2": {
            "request": {
                "action": "query",
                "target": {
                    "features": []
                }
            }
        }
    }
}
