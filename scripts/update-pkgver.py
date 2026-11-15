#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO_MAP = {
    "kclip": "koresent/kclip",
    "kfont": "koresent/kfont",
    "kgreet": "koresent/kgreet",
    "klock": "koresent/klock",
    "korob": "koresent/korob",
    "snap-hud": "koresent/snap-hud",
    "sweep": "koresent/sweep",
    "browser-toolkit": "koresent/browser-toolkit",
}

RELEASE_MAP = {
    "adsum": "yiesko/adsum",
    "ai-file-sorter": "hyperfield/ai-file-sorter",
    "photocraft-companion": "kobaltgit/photocraft-companion",
}

def get_repo_commit_info(repo: str, explicit_commit: str = None) -> tuple[int, str]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"User-Agent": "pkg-repo-sync"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        latest_sha = data[0]["sha"]
        link_header = resp.headers.get("Link", "")
        match = re.search(r"&page=(\d+)>; rel=\"last\"", link_header)
        count = int(match.group(1)) if match else 1

    commit_sha = explicit_commit if explicit_commit else latest_sha
    return count, commit_sha[:7]

def get_latest_release(repo: str) -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"User-Agent": "pkg-repo-sync"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            tags_url = f"https://api.github.com/repos/{repo}/tags?per_page=1"
            req_tags = urllib.request.Request(tags_url, headers=headers)
            with urllib.request.urlopen(req_tags) as resp:
                data = json.loads(resp.read().decode())
                tag = data[0]["name"] if data else ""
        else:
            raise

    cleaned_ver = re.sub(r"^v", "", tag.strip())
    return cleaned_ver

def update_package(pkg: str, explicit_commit: str = None) -> bool:
    pkgbuild_path = os.path.join("packages", pkg, "PKGBUILD")
    if not os.path.isfile(pkgbuild_path):
        print(f"PKGBUILD not found for {pkg} at {pkgbuild_path}", file=sys.stderr)
        return False

    repo = REPO_MAP.get(pkg)
    if not repo:
        print(f"No upstream repo mapping for {pkg}, skipping auto-bump.")
        return False

    try:
        count, short_sha = get_repo_commit_info(repo, explicit_commit)
    except Exception as e:
        print(f"Failed to fetch commit info for {repo}: {e}", file=sys.stderr)
        return False

    with open(pkgbuild_path, "r", encoding="utf-8") as f:
        content = f.read()

    match_ver = re.search(r"^pkgver=([^\n]+)", content, re.MULTILINE)
    if not match_ver:
        print(f"Could not find pkgver in {pkgbuild_path}", file=sys.stderr)
        return False

    current_ver = match_ver.group(1).strip()
    base_ver = current_ver.split(".r")[0]
    new_ver = f"{base_ver}.r{count}.g{short_sha}"

    if current_ver == new_ver:
        print(f"{pkg}: up-to-date ({current_ver})")
        return False

    content = re.sub(r"^pkgver=[^\n]+", f"pkgver={new_ver}", content, flags=re.MULTILINE)
    content = re.sub(r"^pkgrel=[^\n]+", "pkgrel=1", content, flags=re.MULTILINE)

    with open(pkgbuild_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"{pkg}: updated {current_ver} -> {new_ver}")
    return True

def update_release_package(pkg: str) -> bool:
    pkgbuild_path = os.path.join("packages", pkg, "PKGBUILD")
    if not os.path.isfile(pkgbuild_path):
        print(f"PKGBUILD not found for {pkg} at {pkgbuild_path}", file=sys.stderr)
        return False

    repo = RELEASE_MAP.get(pkg)
    if not repo:
        print(f"No release repo mapping for {pkg}, skipping.")
        return False

    try:
        latest_ver = get_latest_release(repo)
    except Exception as e:
        print(f"Failed to fetch release info for {repo}: {e}", file=sys.stderr)
        return False

    if not latest_ver:
        print(f"Could not determine latest version for {repo}", file=sys.stderr)
        return False

    with open(pkgbuild_path, "r", encoding="utf-8") as f:
        content = f.read()

    match_ver = re.search(r"^pkgver=([^\n]+)", content, re.MULTILINE)
    if not match_ver:
        print(f"Could not find pkgver in {pkgbuild_path}", file=sys.stderr)
        return False

    current_ver = match_ver.group(1).strip()
    if current_ver == latest_ver:
        print(f"{pkg}: up-to-date ({current_ver})")
        return False

    content = re.sub(r"^pkgver=[^\n]+", f"pkgver={latest_ver}", content, flags=re.MULTILINE)
    content = re.sub(r"^pkgrel=[^\n]+", "pkgrel=1", content, flags=re.MULTILINE)

    with open(pkgbuild_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"{pkg}: updated {current_ver} -> {latest_ver}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Update PKGBUILD versions from upstream git repositories.")
    parser.add_argument("--package", help="Specific package to update")
    parser.add_argument("--commit", help="Explicit commit hash from webhook")
    parser.add_argument("--check-upstream", action="store_true", help="Check and update release-based packages")
    parser.add_argument("--all", action="store_true", help="Update all mapped packages")
    args = parser.parse_args()

    if args.package:
        if args.package in RELEASE_MAP:
            update_release_package(args.package)
        else:
            update_package(args.package, args.commit)
    elif args.check_upstream:
        for pkg in RELEASE_MAP:
            update_release_package(pkg)
    elif args.all:
        for pkg in REPO_MAP:
            update_package(pkg)
        for pkg in RELEASE_MAP:
            update_release_package(pkg)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
