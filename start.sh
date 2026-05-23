#!/bin/bash
set -e

echo "=== MuelaADS Setup ==="

echo "Installing backend deps..."
pip install -r backend/requirements.txt

echo "Installing frontend deps..."
cd frontend && npm install && cd ..

echo "Starting MuelaADS with PM2..."
pm2 start ecosystem.config.js
pm2 save

echo ""
echo "MuelaADS is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
