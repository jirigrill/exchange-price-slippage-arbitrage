#!/bin/bash

# Bitcoin Arbitrage Monitor - Simple Deployment Script
set -e

echo "🐳 Deploying Bitcoin Arbitrage Monitor..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   sudo apt install docker-compose"
    echo "   # or"
    echo "   sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "   sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Copy environment file if it doesn't exist
if [[ ! -f .env ]]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running!"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after editing .env file (or Ctrl+C to exit)..."
fi

# Build and start containers
echo "🔨 Building Docker image..."
docker-compose build

echo "▶️  Starting containers..."
docker-compose up -d

# Wait for container to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Bitcoin Arbitrage Monitor is running successfully!"
    echo ""
    echo "📊 Container status:"
    docker-compose ps
    echo ""
    echo "📋 Useful commands:"
    echo "  View live logs:      docker-compose logs -f"
    echo "  Stop service:        docker-compose down"
    echo "  Restart service:     docker-compose restart"
    echo "  Update & restart:    git pull && docker-compose build && docker-compose up -d"
    echo "  Access container:    docker-compose exec arbitrage-monitor bash"
    echo ""
    echo "📈 View logs now:"
    docker-compose logs --tail=20
else
    echo "❌ Failed to start containers"
    echo "📋 Check logs for errors:"
    docker-compose logs
    exit 1
fi