"""Quick secret-file pattern scanner."""

import sys
from pathlib import Path

PATTERNS = [
    "kaggle", "access_token", ".env", "secret", "password",
    "credentials", ".tfstate", "*.pem", "*.key",
]

def main() -> int:
    files = Path("git_files.log").read_text().splitlines()
    hits = []
    for name in files:
        clean = name.strip()
        if not clean:
            continue
        for p in PATTERNS:
            if p in clean.lower():
                hits.append((p, clean))
    if hits:
        print("Sensitive path hits:")
        for h in hits:
            print(f"  - pattern={h[0]}  file={h[1]}")
        return 1
    print("PASS – no sensitive files in tracked set.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
