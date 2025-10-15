#!/usr/bin/env bash
set -euo pipefail

# Configurable via environment:
# - VERSION=x.y.z   # explicit version to tag
# - TAG_PREFIX=v    # default 'v'
# - REMOTE=origin   # default 'origin'

REMOTE="${REMOTE:-origin}"
TAG_PREFIX="${TAG_PREFIX:-v}"
VER="${VERSION:-}"

if [[ -z "$VER" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LAST_TAG" ]]; then
    BASE="${LAST_TAG#v}"
    IFS='.' read -r MA MI PA <<< "$BASE"
    MA="${MA:-0}"; MI="${MI:-0}"; PA="${PA:-0}"
    if ! [[ "$MA" =~ ^[0-9]+$ && "$MI" =~ ^[0-9]+$ && "$PA" =~ ^[0-9]+$ ]]; then
      echo "Error: last tag '$LAST_TAG' is not a semantic version (x.y.z)." >&2
      exit 1
    fi
    PA=$((PA + 1))
    VER="${MA}.${MI}.${PA}"
    echo "No VERSION provided; bumping patch from ${LAST_TAG} -> ${VER}"
  else
    VER="0.1.0"
    echo "No VERSION provided and no existing tags; defaulting to ${VER}"
  fi
else
  echo "Using provided VERSION: ${VER}"
fi

TAG="${TAG_PREFIX}${VER}"
echo "Preparing tag ${TAG} (remote ${REMOTE})"

# Ensure clean working tree (no uncommitted changes or untracked files)
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is not clean. Commit, stash, or remove changes before tagging." >&2
  git status --porcelain
  exit 1
fi

# Remove existing tag locally/remote if present
git tag -d "${TAG}" >/dev/null 2>&1 || true
git push "${REMOTE}" --delete "${TAG}" >/dev/null 2>&1 || true

# Create annotated tag and push
git tag -a "${TAG}" -m "Release ${TAG}"
git push "${REMOTE}" "${TAG}"
echo "Tag ${TAG} pushed to ${REMOTE}"
