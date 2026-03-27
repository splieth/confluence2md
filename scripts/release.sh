#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <major|minor|patch>"
    exit 1
fi

bump="$1"

if [[ "$bump" != "major" && "$bump" != "minor" && "$bump" != "patch" ]]; then
    echo "Error: argument must be one of: major, minor, patch"
    exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: working directory is not clean. Commit or stash changes first."
    exit 1
fi

current=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
IFS='.' read -r major minor patch_v <<< "$current"

case "$bump" in
    major) major=$((major + 1)); minor=0; patch_v=0 ;;
    minor) minor=$((minor + 1)); patch_v=0 ;;
    patch) patch_v=$((patch_v + 1)) ;;
esac

new_version="${major}.${minor}.${patch_v}"

sed -i'' -e "s/^version = \"${current}\"/version = \"${new_version}\"/" pyproject.toml

git add pyproject.toml
git commit -m "Release v${new_version}"
git tag "v${new_version}"
git push origin main --tags

echo "Released v${new_version}"
