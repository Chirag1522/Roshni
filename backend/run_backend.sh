#!/bin/bash
# ROSHNI Backend Startup Script

# Kill any existing backend processes
pkill -9 -f "python.*main.py" 2>/dev/null || true
pkill -9 -f "uvicorn.*main:app" 2>/dev/null || true
sleep 2

echo "=========================================="
echo "🚀 Starting ROSHNI Backend..."
echo "=========================================="
echo ""
echo "✅ Admin Wallet: PMXWLGEHMYRRRFVPK7GOCU5TGVEXUBPYLT3XA4JOBCDB4ZDUSP3GD73VTQ"
echo "✅ Balance: ~20 Algo (can fund 10 wallets)"
echo "✅ SUN ASA ID: 756341116"
echo ""
echo "Backend will start in a moment..."
echo "Visit: http://localhost:8000/health to check status"
echo "Frontend: http://localhost:5173"
echo ""
echo "=========================================="
echo ""

cd /home/khushi/roshni/backend

# Activate venv and start
source venv/bin/activate
export PYTHONUNBUFFERED=1

# Start with logging
python main.py 2>&1 | tee backend.log
