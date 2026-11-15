#!/usr/bin/env bash
# One-command LOCAL simulator pilot:
# - first-party static faculty password already created privately
# - creates/trusts a temporary TLS CA inside the iPad Simulator ONLY
# - prompts locally for Basic sandbox meeting ID/passcode and SDK credentials
# - starts localhost-only HTTPS login + authorized Zoom join ticket server
# NO webinar, production Zoom tenant, third-party login or public endpoint.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO"
PY="$HOME/.venvs/doctutorials-ipad-api/bin/python"
ASSIGNMENT="$HOME/.config/doctutorials/ipad-basic-assignment.json"
FACULTY="$HOME/.config/doctutorials/faculty-basic-sandbox.json"
TLS="$HOME/.config/doctutorials/localhost-tls"

if [[ ! -x "$PY" ]]; then
  echo "Missing test/dev venv. Run: python3 -m venv $HOME/.venvs/doctutorials-ipad-api" >&2
  echo "Then: $HOME/.venvs/doctutorials-ipad-api/bin/python -m pip install -r backend/requirements-ipad-dev.txt" >&2
  exit 1
fi
if [[ ! -f "$FACULTY" ]]; then
  echo "Private faculty password not set. First run:" >&2
  echo "python3 -m backend.faculty_password_auth setup --faculty-id sandbox-faculty --display-name 'Sandbox Faculty'" >&2
  exit 1
fi
if ! command -v xcodegen >/dev/null; then
  echo "XcodeGen is required to regenerate the SDK-enabled project." >&2
  exit 1
fi

echo "Preparing local HTTPS trust for the booted iPad Simulator..."
bash "$REPO/ipad/DocTutorialsScreenShare/scripts/setup_local_simulator_https.sh"

if [[ ! -f "$ASSIGNMENT" ]]; then
  echo "Configure your ONE test Meeting in the free Zoom Basic sandbox."
  echo "The Zoom Meeting number and passcode will be requested privately and NOT echoed."
  "$PY" -m backend.local_ipad_sandbox_server setup-assignment \
    --faculty-id sandbox-faculty --session-id ipad-sandbox-class
fi

echo "Regenerating the real SDK-enabled iPad project..."
(
  cd "$REPO/ipad/DocTutorialsScreenShare"
  xcodegen generate --spec project-sdk.yml
  open DocTutorialsScreenShare.xcodeproj
)

echo "Starting your private local HTTPS sandbox backend."
echo "In iPad simulator enter: https://localhost:8443"
echo "Faculty ID: sandbox-faculty"
echo "Assigned session ID: ipad-sandbox-class"
echo "Use the fixed password you set previously (do not share it)."
echo "The next prompts request the separate Meeting SDK General App Client ID/Secret."
"$PY" -m backend.local_ipad_sandbox_server serve-https \
  --faculty-file "$FACULTY" \
  --assignment-file "$ASSIGNMENT" \
  --tls-cert "$TLS/localhost.pem" \
  --tls-key "$TLS/localhost.key" \
  --port 8443
