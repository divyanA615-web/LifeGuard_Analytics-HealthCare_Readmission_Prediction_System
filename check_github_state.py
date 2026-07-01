"""Read public repo metadata via GitHub API (no auth required for public)."""

import json
import urllib.request

API = "https://api.github.com/repos/divyanA615-web/LifeGuard_Analytics-HealthCare_Readmission_Prediction_System"


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "lifeguard-audit"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


try:
    data = fetch()
    print(f"name          : {data['name']}")
    print(f"full_name     : {data['full_name']}")
    print(f"description   : {data.get('description')}")
    print(f"private       : {data['private']}")
    print(f"default_branch: {data['default_branch']}")
    print(f"visibility    : {data.get('visibility')}")
    print(f"open_issues   : {data['open_issues_count']}")
    print(f"size_kb       : {data['size']}")
    print(f"license       : {data.get('license', {}).get('spdx_id') if data.get('license') else 'none'}")
    print(f"pushed_at     : {data['pushed_at']}")
    print(f"created_at    : {data['created_at']}")
    print(f"updated_at    : {data['updated_at']}")
except Exception as e:
    print(f"ERROR: {e}")
