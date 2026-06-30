"""Scan tracked files for actual secret VALUES (not just filenames)."""

import re
from pathlib import Path

PATTERNS = [
    (r"\bnvapi-[A-Za-z0-9_-]{12,}", "NVIDIA API key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key"),
    (r"\bghp_[A-Za-z0-9]{36}\b", "GitHub token"),
    (r"\b8cc41d5d2500d002ff9aef1625774a06\b", "Kaggle secret (literal)"),
    (r"\bsk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]+\b", "OpenAI key"),
    (r"-----BEGIN [A-Z]+ PRIVATE KEY-----", "PEM private key"),
    (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded password"),
]


def main() -> int:
    files = Path("git_files.log").read_text().splitlines()
    hits = []
    for f in files:
        path = Path(f.strip())
        if not path.exists():
            continue
        if path.stat().st_size > 2_000_000:  # skip >2MB
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat, name in PATTERNS:
            for m in re.finditer(pat, content):
                hits.append((name, str(path), m.group(0)[:40] + "…"))
    if hits:
        print("Content hits:")
        for h in hits:
            print(f"  - {h[0]} in {h[1]}: {h[2]}")
        return 1
    print("PASS – no secret values detected in tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
