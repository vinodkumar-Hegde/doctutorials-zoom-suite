#!/usr/bin/env bash
# Prepares the user-downloaded iOS Zoom Meeting SDK for an opt-in Xcode build.
# Never uploads vendor binaries or handles Zoom credentials.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd -P)"
source_dir="$HOME/Downloads/DocTutorialsZoomSDK"
if [[ $# -ge 1 ]]; then
  source_dir="$1"
fi
if [[ ! -d "$source_dir" ]]; then
  echo "ERROR: Extracted Zoom iOS SDK directory not found." >&2
  exit 1
fi
source_dir="$(cd "$source_dir" && pwd -P)"

for item in version.txt lib/MobileRTC.xcframework lib/MobileRTCResources.bundle lib/MobileRTCScreenShare.xcframework; do
  if [[ ! -e "$source_dir/$item" ]]; then
    printf 'ERROR: Required SDK component missing: %s\n' "$item" >&2
    exit 1
  fi
done

# The proprietary SDK remains in Downloads, outside the Git repository.
target="$root/vendor/ZoomMeetingSDK"
mkdir -p "$(dirname "$target")"
if [[ -L "$target" ]]; then
  if [[ "$(readlink "$target")" != "$source_dir" ]]; then
    echo "ERROR: A different SDK symlink is already present. Refusing replacement." >&2
    exit 1
  fi
elif [[ -e "$target" ]]; then
  echo "ERROR: SDK destination already exists and is not a symlink. Refusing replacement." >&2
  exit 1
else
  ln -s "$source_dir" "$target"
fi

echo "SDK framework paths: VERIFIED"
printf 'SDK version.txt: '
head -n 1 "$source_dir/version.txt"
if [[ -d "$source_dir/lib/zoomcml.xcframework" ]]; then
  echo "Optional zoomcml XCFramework: FOUND (physical-device use to be verified)"
else
  echo "Optional zoomcml XCFramework: NOT FOUND"
fi
echo "Local vendor symlink: READY (ignored by Git)"
echo "No Zoom binaries or secrets were copied to Git."
echo "Next: xcodegen generate --spec project-sdk.yml"
