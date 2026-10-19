#!/usr/bin/env bash
# Publish a release asset, retrying with exponential backoff.
#
# GitHub's API intermittently times out under load, and action-gh-release gives
# up on the first error — which leaves a release holding only the asset of
# whichever job happened to win the race. Both jobs call this, so the create
# call below is allowed to lose: the next attempt finds the release and uploads.

set -uo pipefail

tag=${1:?usage: publish-release.sh <tag> <asset>}
asset=${2:?usage: publish-release.sh <tag> <asset>}

attempts=5
delay=5

for ((attempt = 1; attempt <= attempts; attempt++)); do
  if gh release view "$tag" >/dev/null 2>&1; then
    gh release upload "$tag" "$asset" --clobber
  else
    gh release create "$tag" "$asset" --title "$tag" --verify-tag
  fi && { echo "published $asset to release $tag"; exit 0; }

  if ((attempt == attempts)); then
    break
  fi
  echo "publish attempt $attempt/$attempts failed; retrying in ${delay}s"
  sleep "$delay"
  delay=$((delay * 2))
done

echo "::error::could not publish $asset to release $tag after $attempts attempts"
exit 1
