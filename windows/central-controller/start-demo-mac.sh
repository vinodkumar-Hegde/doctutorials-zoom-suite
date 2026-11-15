#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import PIL' || { echo 'Pillow required: python3 -m pip install Pillow'; exit 1; }
command -v ffmpeg >/dev/null || { echo 'FFmpeg required (e.g. brew install ffmpeg)'; exit 1; }
exec python3 controller.py --demo
