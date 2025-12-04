#!/bin/bash

# Gabagool Dashboard Start Script

echo "🚀 Starting Gabagool Volatility Arbitrage Dashboard"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚙️  Creating .env.local from example..."
    cp .env.local.example .env.local
    echo "✅ Created .env.local - update with your backend URL if needed"
    echo ""
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Warning: Backend not detected on http://localhost:8000"
    echo "   Make sure your backend API is running before using the dashboard"
fi

echo ""
echo "🎯 Starting development server..."
echo "   Dashboard will be available at: http://localhost:3000"
echo ""

npm run dev
