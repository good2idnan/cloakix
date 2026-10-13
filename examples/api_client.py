"""Call the Cloakix REST API.

Start the server first:  cloakix serve
Then run:                python examples/api_client.py
"""

import json
import urllib.request

payload = {"text": "اسمي أحمد العتيبي، جوالي 0551234567، رقم الملف 778812"}
request = urllib.request.Request(
    "http://127.0.0.1:8000/v1/mask",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request) as response:
    print(json.dumps(json.load(response), ensure_ascii=False, indent=2))
