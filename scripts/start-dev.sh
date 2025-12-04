#!/bin/bash

# Gabagool Development Startup Script
# This script checks prerequisites and starts the development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          🍖 Gabagool - Development Startup                 ║"
echo "║     Polymarket Volatility Arbitrage Bot                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to check if Docker is running
check_docker() {
    echo -e "${BLUE}[1/5] Checking Docker...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed!${NC}"
        echo -e "${YELLOW}Please install Docker Desktop from: https://www.docker.com/products/docker-desktop${NC}"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker is not running!${NC}"
        echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker is running${NC}"
}

# Function to check if docker-compose is available
check_docker_compose() {
    echo -e "${BLUE}[2/5] Checking Docker Compose...${NC}"

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed!${NC}"
        echo -e "${YELLOW}Please install Docker Compose from: https://docs.docker.com/compose/install/${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker Compose is available${NC}"
}

# Function to check and create .env file
check_env_file() {
    echo -e "${BLUE}[3/5] Checking environment configuration...${NC}"

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found!${NC}"
        echo -e "${BLUE}Creating .env from .env.example...${NC}"

        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            echo -e "${GREEN}✓ Created .env file${NC}"
            echo -e "${YELLOW}"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "⚠️  IMPORTANT: Configure your .env file before proceeding!"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "You need to add your Polymarket credentials:"
            echo "  - POLYMARKET_API_KEY"
            echo "  - POLYMARKET_API_SECRET"
            echo "  - PRIVATE_KEY (your Polygon wallet)"
            echo ""
            echo "Edit the file: nano .env"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo -e "${NC}"

            read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
        else
            echo -e "${RED}❌ .env.example file not found!${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ .env file exists${NC}"

        # Check if .env has placeholder values
        if grep -q "your_api_key_here" "$PROJECT_ROOT/.env"; then
            echo -e "${YELLOW}"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "⚠️  WARNING: .env contains placeholder values!"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Please update with your real credentials before starting."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo -e "${NC}"

            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}Exiting. Please configure .env and try again.${NC}"
                exit 1
            fi
        fi
    fi
}

# Function to pull/build Docker images
prepare_images() {
    echo -e "${BLUE}[4/5] Preparing Docker images...${NC}"
    echo -e "${YELLOW}This may take a few minutes on first run...${NC}"

    docker-compose build --quiet

    echo -e "${GREEN}✓ Docker images ready${NC}"
}

# Function to start services
start_services() {
    echo -e "${BLUE}[5/5] Starting services...${NC}"

    # Stop any existing containers
    docker-compose down --remove-orphans &> /dev/null || true

    # Start services in detached mode
    docker-compose up -d

    echo -e "${GREEN}✓ Services started${NC}"
}

# Function to wait for services to be healthy
wait_for_services() {
    echo -e "${BLUE}Waiting for services to be ready...${NC}"

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "Up"; then
            # Check if backend is responding
            if curl -s http://localhost:8000/health &> /dev/null; then
                echo -e "${GREEN}✓ All services are ready!${NC}"
                return 0
            fi
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo -e "${YELLOW}⚠️  Services started but may not be fully ready yet.${NC}"
    echo -e "${YELLOW}Check logs with: make logs${NC}"
}

# Function to open browser
open_browser() {
    echo -e "${BLUE}Opening dashboard in browser...${NC}"

    sleep 3  # Wait a bit for dashboard to be ready

    # Try different commands depending on OS
    if command -v open &> /dev/null; then
        open http://localhost:3000 &> /dev/null || true
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000 &> /dev/null || true
    elif command -v start &> /dev/null; then
        start http://localhost:3000 &> /dev/null || true
    fi
}

# Function to display final information
display_info() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  🎉 Gabagool is Running!                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${BLUE}📊 Dashboard:${NC}      http://localhost:3000"
    echo -e "${BLUE}📚 API Docs:${NC}       http://localhost:8000/docs"
    echo -e "${BLUE}🔧 API Endpoint:${NC}   http://localhost:8000"
    echo -e "${BLUE}💾 Redis:${NC}          localhost:6379"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "${BLUE}  make logs${NC}              - View all logs"
    echo -e "${BLUE}  make logs-backend${NC}      - View backend logs"
    echo -e "${BLUE}  make logs-dashboard${NC}    - View dashboard logs"
    echo -e "${BLUE}  make stop${NC}              - Stop all services"
    echo -e "${BLUE}  make clean${NC}             - Stop and remove containers"
    echo -e "${BLUE}  make ps${NC}                - Show service status"
    echo ""
    echo -e "${RED}⚠️  Risk Warning:${NC}"
    echo -e "${YELLOW}Trading involves risk of loss. Never trade with funds you can't afford to lose.${NC}"
    echo -e "${YELLOW}Start with small position sizes and monitor constantly.${NC}"
    echo ""
    echo -e "${GREEN}Press Ctrl+C to stop following logs, or run 'make stop' to stop services.${NC}"
    echo ""
}

# Main execution flow
main() {
    check_docker
    check_docker_compose
    check_env_file
    prepare_images
    start_services
    wait_for_services
    display_info
    open_browser

    # Follow logs
    echo -e "${BLUE}Following logs (Ctrl+C to exit)...${NC}"
    echo ""
    docker-compose logs -f
}

# Trap Ctrl+C and clean exit
trap 'echo -e "\n${BLUE}To stop services, run: ${GREEN}make stop${NC}"' INT

# Run main function
main
