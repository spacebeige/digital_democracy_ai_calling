#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
AUDIO_FILE="${1:-}"

if [[ -z "$AUDIO_FILE" ]]; then
  echo "Usage: ./smoke_test.sh /absolute/path/to/sample.wav"
  exit 1
fi

if [[ ! -f "$AUDIO_FILE" ]]; then
  echo "Audio file not found: $AUDIO_FILE"
  exit 1
fi

echo "[1/3] Checking backend health..."
curl -sS "$BACKEND_URL/" | cat

echo "\n[2/3] Checking downstream service health..."
curl -sS "$BACKEND_URL/calls/health" | cat

echo "\n[3/3] Running end-to-end call turn..."
response="$(curl -sS -X POST "$BACKEND_URL/calls/handle-turn" \
  -F "audio_file=@$AUDIO_FILE" \
  -F "call_id=smoke-test-call")"

echo "$response" | cat

echo "\nSmoke test finished."
