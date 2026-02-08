#!/bin/bash

# 1. Start Backend (FastAPI) in background
# We bind to 127.0.0.1 because only Streamlit needs to talk to it locally.
echo "🚀 Starting Backend on http://127.0.0.1:8000..."
uvicorn server:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for Backend to initialize (Loop until port 8000 is open)
echo "⏳ Waiting for backend to start..."
for i in {1..120}; do
    if curl -s http://127.0.0.1:8000 > /dev/null; then
        echo "✅ Backend is UP!"
        break
    fi
    echo "zzz... ($i/120)"
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend DIED prematurely."
        break
    fi
    sleep 1
done

# Check if backend failed to start (Timeout or Crash)
if ! curl -s http://127.0.0.1:8000 > /dev/null; then
    echo "❌ Backend FAILED to start (Timeout or Crash). Showing logs:"
    cat backend.log
    exit 1
fi

# 2. Start Frontend (Streamlit) in foreground
# Render/Heroku provide $PORT. Streamlit needs to bind to it.
echo "🚀 Starting Frontend on port ${PORT:-8501}..."
streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0

# Cleanup trap
trap "kill $BACKEND_PID" EXIT
