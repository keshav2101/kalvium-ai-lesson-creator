#!/usr/bin/env bash
# start.sh — Start both the backend and frontend dev servers
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# Copy .env if .env doesn't exist yet
if [ ! -f "$ROOT/.env" ] && [ -f "$ROOT/.env.example" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "⚠️  Copied .env.example → .env  (add your API keys to .env)"
fi

# Source .env so the backend picks it up
if [ -f "$ROOT/.env" ]; then
  set -a && source "$ROOT/.env" && set +a
fi

echo "── Starting FastAPI backend on http://localhost:8000 ──"
cd "$BACKEND"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "── Starting Next.js frontend on http://localhost:3000 ──"
cd "$FRONTEND"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers running."
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop both."

trap "echo 'Stopping…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" SIGINT SIGTERM
wait

