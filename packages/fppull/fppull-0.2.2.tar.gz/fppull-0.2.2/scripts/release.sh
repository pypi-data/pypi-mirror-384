#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/release.sh v0.1.0 "Short title" ["Longer release notes..."]
# If the 3rd arg is omitted, notes are generated from git log since last tag.

VERSION="${1:-}"
TITLE="${2:-${1:-}}"
NOTES_IN="${3:-}"

if [[ -z "${VERSION}" || ! "${VERSION}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: scripts/release.sh vX.Y.Z \"Title\" [Notes]"
  exit 2
fi

# Safety checks
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree not clean. Commit or stash first."
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${CURRENT_BRANCH}" != "main" ]]; then
  echo "❌ Please release from main (you are on: ${CURRENT_BRANCH})"
  exit 1
fi

# Run local guardrails (fast; same as your pre-push)
echo "▶ pre-commit..."
pre-commit run --from-ref origin/main --to-ref HEAD || { echo "pre-commit failed"; exit 1; }

echo "▶ tests..."
./scripts/ci.sh test

echo "▶ contract tests..."
./scripts/ci.sh contracts

# Compute notes if not provided
if [[ -z "${NOTES_IN}" ]]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "${LAST_TAG}" ]]; then
    RANGE="${LAST_TAG}..HEAD"
  else
    RANGE="$(git rev-list --max-parents=0 HEAD)..HEAD"
  fi
  NOTES_FILE="$(mktemp)"
  {
    echo "### Changes"
    echo
    git log --pretty='- %s (%h)' ${RANGE}
  } > "${NOTES_FILE}"
else
  NOTES_FILE="$(mktemp)"
  printf "%s\n" "${NOTES_IN}" > "${NOTES_FILE}"
fi

# Create annotated tag and push
echo "▶ tagging ${VERSION}…"
git tag -a "${VERSION}" -m "${TITLE}"
git push origin "${VERSION}"

# Create GitHub release with notes
echo "▶ creating GitHub release…"
gh release create "${VERSION}" -t "${TITLE}" -F "${NOTES_FILE}"

echo "✅ Release ${VERSION} published."
