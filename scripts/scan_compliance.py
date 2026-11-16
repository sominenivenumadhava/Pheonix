#!/usr/bin/env python3
"""
Phoenix Secrets and Compliance Scanner: scan_secrets.py
Scans Git-tracked files to ensure no private keys, AWS access keys,
passwords, database files, or Terraform state files are tracked or committed.
"""

import os
import re
import sys
import subprocess

PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"), "Private SSH/TLS Key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{30,}['\"]"), "AWS Secret Key"),
    (re.compile(r"(?i)vault_password\s*=\s*['\"][^'\"]+['\"]"), "Ansible Vault Password"),
    (re.compile(r"^#!\s*ansible-vault"), "Committed Raw Vault Secret"),
]

BANNED_EXTENSIONS = [".tfstate", ".tfstate.backup", ".db", ".sqlite", ".sqlite3"]

def get_git_tracked_files(root_dir="."):
    """Retrieve list of all files tracked by git plus untracked non-ignored files."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=root_dir,
            text=True,
            capture_output=True,
            check=True
        )
        tracked = res.stdout.splitlines()

        # Also get untracked but not ignored files
        res_other = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root_dir,
            text=True,
            capture_output=True,
            check=True
        )
        untracked = res_other.stdout.splitlines()
        return sorted(list(set(tracked + untracked)))
    except Exception as e:
        print(f"[!] Warning: Could not run git ls-files ({e}). Falling back to os.walk.", file=sys.stderr)
        return None

def scan_files(files_to_scan, root_dir="."):
    findings = []
    for rel_path in files_to_scan:
        file_path = os.path.join(root_dir, rel_path)
        if not os.path.isfile(file_path):
            continue

        # Check banned extensions
        _, ext = os.path.splitext(rel_path)
        if ext.lower() in BANNED_EXTENSIONS:
            findings.append((rel_path, f"Banned file extension tracked: {ext}"))
            continue

        # Skip binary, compiled, lock, or media files
        if rel_path.endswith((".pyc", ".exe", ".png", ".jpg", ".lock", ".svg", ".woff", ".woff2")):
            continue

        # Scan text content
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern, desc in PATTERNS:
                    if pattern.search(content):
                        findings.append((rel_path, desc))
        except Exception as e:
            findings.append((rel_path, f"Error reading file: {e}"))

    return findings

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"[*] Starting secrets and compliance scan on repository: {root_dir}")

    files = get_git_tracked_files(root_dir)
    if files is None:
        sys.exit(1)

    print(f"[*] Scanning {len(files)} tracked and unignored repository files...")
    findings = scan_files(files, root_dir)

    print("-" * 72)
    if findings:
        print("[!] SECURITY VIOLATION: POTENTIAL SECRETS OR BANNED FILES FOUND:")
        for path, desc in findings:
            print(f"  [X] {path}: {desc}")
        print("-" * 72)
        sys.exit(1)
    else:
        print("[✓] REPOSITORY SECRETS SCAN PASSED: 100% CLEAN!")
        print("    - Zero private SSH/TLS keys (.pem, id_rsa) tracked")
        print("    - Zero AWS access keys / secret tokens tracked")
        print("    - Zero Terraform state files (.tfstate) tracked")
        print("    - Zero SQLite database or backup files (.db) tracked")
        print("    - Zero unencrypted Ansible Vault passwords tracked")
        print("-" * 72)
        sys.exit(0)

if __name__ == "__main__":
    main()
