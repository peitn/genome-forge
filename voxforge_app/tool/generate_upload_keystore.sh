#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-$HOME/upload-keystore.jks}"
echo "Creating Android upload keystore at: $OUT"
keytool -genkey -v \
  -keystore "$OUT" \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias upload

echo "Done. Copy android/key.properties.example to android/key.properties and set storeFile=$OUT"
