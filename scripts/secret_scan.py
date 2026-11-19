"""Repository Secret Pattern Scanner.
Scans tracked source files for accidental credential patterns (AWS keys, GitHub PATs, private keys).
"""
from pathlib import Path
import re
import sys

SECRET_PATTERNS = re.compile(
    r"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    scanned = 0
    for py_file in root.rglob("*.py"):
        if py_file.name == "secret_scan.py":
            continue
        scanned += 1
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if SECRET_PATTERNS.search(content):
            print(f"[SECRET-SCAN FAIL] Potential hardcoded credential detected in {py_file}")
            sys.exit(1)
    print(f"[SECRET-SCAN PASS] Scanned {scanned} Python source files: 0 hardcoded credentials detected.")


if __name__ == "__main__":
    main()
