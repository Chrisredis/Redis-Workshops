#!/bin/bash

# Redis Active-Active Fraud Detection Demo Launcher
# This script sets up and runs the complete fraud detection demo

echo "🛡️ Redis Active-Active Fraud Detection Demo"
echo "============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is available"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 is available"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Start Redis containers
echo "🐳 Starting Redis containers..."

# Stop existing containers if they exist
docker stop redis-store-a redis-store-b 2>/dev/null
docker rm redis-store-a redis-store-b 2>/dev/null

# Start Store A (port 6379)
docker run -d --name redis-store-a -p 6379:6379 redis/redis-stack:latest

if [ $? -ne 0 ]; then
    echo "❌ Failed to start Redis Store A"
    exit 1
fi

# Start Store B (port 6380)
docker run -d --name redis-store-b -p 6380:6379 redis/redis-stack:latest

if [ $? -ne 0 ]; then
    echo "❌ Failed to start Redis Store B"
    exit 1
fi

echo "✅ Redis containers started"
echo "   Store A: localhost:6379"
echo "   Store B: localhost:6380"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
sleep 5

# Start the demo
echo "🚀 Starting fraud detection demo..."
echo ""
echo "📊 Dashboard will be available at: http://localhost:8080"
echo "🏪 Store A POS: Legitimate transactions with photo verification"
echo "🔓 Store B POS: Compromised system for fraud simulation"
echo ""
echo "Press Ctrl+C to stop the demo"
echo ""

# Run the demo
python3 run_demo.py

# Cleanup on exit
echo ""
echo "🧹 Cleaning up..."
docker stop redis-store-a redis-store-b 2>/dev/null
docker rm redis-store-a redis-store-b 2>/dev/null
echo "✅ Cleanup completed"
