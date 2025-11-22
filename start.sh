#!/bin/bash

# OUTREACH EHR - Launch Script
# Starts both backend and frontend servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏥 Starting OUTREACH EHR..."
echo ""

# Kill any existing servers
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*run.py" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
sleep 1

# Start backend
echo "🔧 Starting backend server..."
cd "$SCRIPT_DIR/backend"
nohup "$SCRIPT_DIR/.venv/bin/python" run.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Start frontend
echo "🎨 Starting frontend server..."
cd "$SCRIPT_DIR/frontend"
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait a moment for servers to start
echo ""
echo "⏳ Waiting for servers to start..."
sleep 5

# Check if servers are running
echo ""
echo "📊 Server Status:"
if ps -p $BACKEND_PID > /dev/null; then
    echo "   ✅ Backend running (PID $BACKEND_PID)"
else
    echo "   ❌ Backend failed to start - check /tmp/backend.log"
    exit 1
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo "   ✅ Frontend running (PID $FRONTEND_PID)"
else
    echo "   ❌ Frontend failed to start - check /tmp/frontend.log"
    exit 1
fi

echo ""
echo "📋 Demo Credentials:"
echo "   RN:         nurse.jane / password123"
echo "   LPN:        nurse.bob / password123"
echo "   Pharmacist: pharm.sarah / password123"
echo "   Admin:      admin.mike / password123"
echo "   CNA:        cna.maria / password123"
echo "   HHA:        hha.david / password123"
echo ""
echo "🚀 Launching browser in kiosk mode..."
echo "   Close the browser window to stop the application"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "python.*run.py" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true
    echo "✅ Shutdown complete"
    exit 0
}

# Set trap to cleanup when script exits
trap cleanup EXIT INT TERM

# Detect browser and launch in kiosk mode
if command -v google-chrome &> /dev/null; then
    google-chrome --kiosk --start-fullscreen http://localhost:3000
elif command -v chromium-browser &> /dev/null; then
    chromium-browser --kiosk --start-fullscreen http://localhost:3000
elif command -v chromium &> /dev/null; then
    chromium --kiosk --start-fullscreen http://localhost:3000
elif command -v firefox &> /dev/null; then
    firefox --kiosk http://localhost:3000
else
    echo "⚠️  No supported browser found. Please open http://localhost:3000 manually"
    echo ""
    echo "📝 Logs:"
    echo "   Backend:  tail -f /tmp/backend.log"
    echo "   Frontend: tail -f /tmp/frontend.log"
    echo ""
    echo "Press Ctrl+C to stop servers"
    # Keep script running
    wait
fi

# When browser closes, cleanup will run automatically via trap
