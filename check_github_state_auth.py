"""Check repo details with auth token (also verifies token works)."""

import json
import urllib.request

TOKEN = "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"
API = "https://api.github.com/repos/divyanA615-web/LifeGuard_Analytics-HealthCare_Readmission_Prediction_System"

req = urllib.request.Request(API, headers={
    "User-Agent": "lifeguard-audit",
    "Authorization": f"Bearer {TOKEN}"
})
try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
        print(f"name          : {data['name']}")
        print(f"private       : {data['private']}")
        print(f"default_branch: {data['default_branch']}")
        print(f"license       : {data.get('license', {}).get('spdx_id') if data.get('license') else 'none'}")
        print(f"description   : {data.get('description')}")
        print(f"visibility    : {data.get('visibility')}")
except Exception as e:
    print(f"ERROR: {e}")
