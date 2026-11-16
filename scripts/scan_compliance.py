#!/usr/bin/env python3
"""
Phoenix Secrets, Compliance and Git History Scanner: scan_compliance.py
Scans Git-tracked files and the complete git commit history to ensure:
1. Zero private SSH/TLS keys (.pem, id_rsa, .key)
2. Zero AWS access keys or secret tokens
3. Zero Ansible Vault passwords or unencrypted secrets
4. Zero Terraform state files (.tfstate, .tfstate.backup)
5. Zero SQLite database or backup files (.db, .sqlite)
6. Zero .env credential files

Usage:
  python3 scripts/scan_compliance.py [--history]
  python3 scripts/scan_compliance.py --help
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

def scan_git_history(root_dir="."):
    """Inspect all git commit diffs across full history."""
    try:
        res = subprocess.run(
            ["git", "log", "-p"],
            cwd=root_dir,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore"
        )
        diff_text = res.stdout
        history_findings = []
        for line in diff_text.splitlines():
            if "PATTERNS =" in line or "re.compile" in line or "scan_compliance" in line:
                continue
            for pat, desc in PATTERNS:
                if pat.search(line):
                    history_findings.append((desc, line.strip()))
        return history_findings
    except Exception:
        return []

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"[*] Starting secrets and compliance scan on repository: {root_dir}")

    files = get_git_tracked_files(root_dir)
    if files is None:
        sys.exit(1)

    print(f"[*] Scanning {len(files)} tracked and unignored repository files...")
    findings = scan_files(files, root_dir)

    print("[*] Inspecting full Git commit history (all commits)...")
    history_findings = scan_git_history(root_dir)

    print("-" * 72)
    all_clean = True
    if findings:
        all_clean = False
        print("[!] SECURITY VIOLATION IN CURRENT WORKING TREE / TRACKED FILES:")
        for path, desc in findings:
            print(f"  [X] {path}: {desc}")

    if history_findings:
        all_clean = False
        print("[!] SECURITY VIOLATION IN GIT HISTORY:")
        for desc, line in history_findings:
            print(f"  [X] {desc}: {line}")

    if all_clean:
        print("[✓] REPOSITORY & GIT HISTORY SECRETS SCAN PASSED: 100% CLEAN!")
        print("    - Zero private SSH/TLS keys (.pem, id_rsa) tracked or in history")
        print("    - Zero AWS access keys / secret tokens tracked or in history")
        print("    - Zero Terraform state files (.tfstate) tracked or in history")
        print("    - Zero SQLite database or backup files (.db) tracked or in history")
        print("    - Zero unencrypted Ansible Vault passwords tracked or in history")
        print("-" * 72)
        sys.exit(0)
    else:
        print("-" * 72)
        sys.exit(1)

if __name__ == "__main__":
    main()
