#!/usr/bin/env bash
# Basic sandbox iPad Simulator ONLY: create a short-lived local HTTPS CA and
# leaf certificate, then trust that CA in the booted Simulator keychain.
# No external identity provider, no Zoom credentials or production trust store.
set -euo pipefail
umask 077

CERT_DIR="$HOME/.config/doctutorials/localhost-tls"
ROOT_CERT="$CERT_DIR/sandbox-root-ca.pem"
ROOT_KEY="$CERT_DIR/sandbox-root-ca.key"
LEAF_CERT="$CERT_DIR/localhost.pem"
LEAF_KEY="$CERT_DIR/localhost.key"

if [[ -e "$ROOT_CERT" || -e "$ROOT_KEY" || -e "$LEAF_CERT" || -e "$LEAF_KEY" ]]; then
  if [[ ! -f "$ROOT_CERT" || ! -f "$LEAF_CERT" || ! -f "$LEAF_KEY" ]]; then
    echo "Partial TLS config detected: do not overwrite private keys." >&2
    exit 1
  fi
  echo "Using existing local HTTPS development certificates."
else
  mkdir -p "$CERT_DIR"
  cat > "$CERT_DIR/ca.cnf" <<'EOF'
[req]
prompt = no
distinguished_name = dn
x509_extensions = v3_ca
[dn]
CN = DocTutorials iPad Simulator ONLY Temporary CA
[v3_ca]
basicConstraints = critical, CA:TRUE
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
EOF
  cat > "$CERT_DIR/leaf.ext" <<'EOF'
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:localhost, IP:127.0.0.1
EOF
  echo "Generating short-lived localhost-only TLS certificates..."
  openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 14 \
    -keyout "$ROOT_KEY" -out "$ROOT_CERT" -config "$CERT_DIR/ca.cnf" \
    >/dev/null 2>&1
  openssl req -newkey rsa:2048 -sha256 -nodes \
    -keyout "$LEAF_KEY" -out "$CERT_DIR/localhost.csr" \
    -subj "/CN=localhost" >/dev/null 2>&1
  openssl x509 -req -in "$CERT_DIR/localhost.csr" \
    -CA "$ROOT_CERT" -CAkey "$ROOT_KEY" -CAcreateserial \
    -out "$LEAF_CERT" -days 14 -sha256 \
    -extfile "$CERT_DIR/leaf.ext" >/dev/null 2>&1
  chmod 600 "$ROOT_KEY" "$LEAF_KEY"
  rm -f "$CERT_DIR/ca.cnf" "$CERT_DIR/leaf.ext" "$CERT_DIR/localhost.csr"
fi

echo "Trusting the temporary root CA in the currently BOOTED iPad Simulator only."
xcrun simctl keychain booted add-root-cert "$ROOT_CERT"

echo "Local TLS setup complete. No Mac/physical-iPad system trust change was made."
echo "Server TLS certificate: $LEAF_CERT"
echo "Server TLS private key: $LEAF_KEY"
echo "Never share/commit any keys, Zoom credentials, or local assignment files."
