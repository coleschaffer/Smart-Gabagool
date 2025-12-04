#!/bin/bash

# Gabagool Setup Script
# This script checks prerequisites and prepares the development environment

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
echo "║            🍖 Gabagool - Setup & Installation              ║"
echo "║        Polymarket Volatility Arbitrage Bot                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print section headers
print_section() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to get version
get_version() {
    $1 2>&1 | head -n 1
}

# Check Docker
check_docker() {
    print_section "Checking Docker Installation"

    if command_exists docker; then
        local version=$(docker --version)
        echo -e "${GREEN}✓ Docker installed: $version${NC}"

        if docker info &> /dev/null; then
            echo -e "${GREEN}✓ Docker daemon is running${NC}"
        else
            echo -e "${RED}✗ Docker daemon is not running${NC}"
            echo -e "${YELLOW}  Please start Docker Desktop and run this script again${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo -e "${YELLOW}  Install from: https://www.docker.com/products/docker-desktop${NC}"
        exit 1
    fi
}

# Check Docker Compose
check_docker_compose() {
    print_section "Checking Docker Compose"

    if command_exists docker-compose; then
        local version=$(docker-compose --version)
        echo -e "${GREEN}✓ Docker Compose installed: $version${NC}"
    else
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        echo -e "${YELLOW}  Install from: https://docs.docker.com/compose/install/${NC}"
        exit 1
    fi
}

# Check Node.js (optional, for local development)
check_nodejs() {
    print_section "Checking Node.js (Optional for Local Dev)"

    if command_exists node; then
        local version=$(node --version)
        echo -e "${GREEN}✓ Node.js installed: $version${NC}"

        if command_exists npm; then
            local npm_version=$(npm --version)
            echo -e "${GREEN}✓ npm installed: $npm_version${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Node.js not installed${NC}"
        echo -e "${YELLOW}  Not required for Docker setup, but useful for local development${NC}"
        echo -e "${YELLOW}  Install from: https://nodejs.org/${NC}"
    fi
}

# Check Python (optional, for local development)
check_python() {
    print_section "Checking Python (Optional for Local Dev)"

    if command_exists python3; then
        local version=$(python3 --version)
        echo -e "${GREEN}✓ Python installed: $version${NC}"

        if command_exists pip3; then
            local pip_version=$(pip3 --version | awk '{print $2}')
            echo -e "${GREEN}✓ pip installed: $pip_version${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Python 3 not installed${NC}"
        echo -e "${YELLOW}  Not required for Docker setup, but useful for local development${NC}"
        echo -e "${YELLOW}  Install from: https://www.python.org/downloads/${NC}"
    fi
}

# Create .env file
setup_env_file() {
    print_section "Setting Up Environment Configuration"

    if [ -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${YELLOW}⚠ .env file already exists${NC}"
        read -p "Overwrite with template? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            echo -e "${GREEN}✓ .env file updated from template${NC}"
        else
            echo -e "${BLUE}Keeping existing .env file${NC}"
        fi
    else
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            echo -e "${GREEN}✓ Created .env file from template${NC}"
        else
            echo -e "${RED}✗ .env.example not found!${NC}"
            exit 1
        fi
    fi

    echo -e "${YELLOW}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  IMPORTANT: You must configure .env before starting!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Required credentials:"
    echo "  1. POLYMARKET_API_KEY       - Get from Polymarket settings"
    echo "  2. POLYMARKET_API_SECRET    - Get from Polymarket settings"
    echo "  3. POLYMARKET_API_PASSPHRASE - Get from Polymarket settings"
    echo "  4. PRIVATE_KEY              - Your Polygon wallet private key"
    echo ""
    echo "Edit with: nano .env"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

# Pull Docker images
pull_docker_images() {
    print_section "Pulling Docker Images"

    echo -e "${BLUE}Pulling base images (this may take a few minutes)...${NC}"

    docker-compose pull

    echo -e "${GREEN}✓ Docker images pulled successfully${NC}"
}

# Create necessary directories
create_directories() {
    print_section "Creating Project Directories"

    local dirs=(
        "$PROJECT_ROOT/backend"
        "$PROJECT_ROOT/dashboard"
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/data"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo -e "${GREEN}✓ Created: $dir${NC}"
        else
            echo -e "${BLUE}Exists: $dir${NC}"
        fi
    done
}

# Check file permissions
check_permissions() {
    print_section "Checking File Permissions"

    # Make scripts executable
    chmod +x "$PROJECT_ROOT/scripts/start-dev.sh" 2>/dev/null || true
    chmod +x "$PROJECT_ROOT/scripts/setup.sh" 2>/dev/null || true

    echo -e "${GREEN}✓ Script permissions updated${NC}"
}

# Test Docker connectivity
test_docker() {
    print_section "Testing Docker Setup"

    echo -e "${BLUE}Testing Docker with a simple container...${NC}"

    if docker run --rm hello-world &> /dev/null; then
        echo -e "${GREEN}✓ Docker is working correctly${NC}"
    else
        echo -e "${RED}✗ Docker test failed${NC}"
        echo -e "${YELLOW}  Please check Docker installation and try again${NC}"
        exit 1
    fi
}

# Display system information
show_system_info() {
    print_section "System Information"

    echo -e "${BLUE}Operating System:${NC} $(uname -s)"
    echo -e "${BLUE}Architecture:${NC} $(uname -m)"
    echo -e "${BLUE}Docker Version:${NC} $(docker --version | awk '{print $3}' | sed 's/,//')"
    echo -e "${BLUE}Docker Compose Version:${NC} $(docker-compose --version | awk '{print $4}' | sed 's/,//')"

    if command_exists node; then
        echo -e "${BLUE}Node.js Version:${NC} $(node --version)"
    fi

    if command_exists python3; then
        echo -e "${BLUE}Python Version:${NC} $(python3 --version | awk '{print $2}')"
    fi

    echo -e "${BLUE}Available Disk Space:${NC} $(df -h . | awk 'NR==2 {print $4}')"
}

# Print next steps
print_next_steps() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                   Setup Complete! 🎉                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo -e "${BLUE}1.${NC} Configure your .env file:"
    echo -e "   ${GREEN}nano .env${NC}"
    echo ""
    echo -e "${BLUE}2.${NC} Get your Polymarket API credentials:"
    echo -e "   ${GREEN}https://polymarket.com/settings/api${NC}"
    echo ""
    echo -e "${BLUE}3.${NC} Start the development environment:"
    echo -e "   ${GREEN}./scripts/start-dev.sh${NC}"
    echo -e "   or"
    echo -e "   ${GREEN}make dev${NC}"
    echo ""
    echo -e "${BLUE}4.${NC} Access the dashboard:"
    echo -e "   ${GREEN}http://localhost:3000${NC}"
    echo ""
    echo -e "${BLUE}5.${NC} Read the documentation:"
    echo -e "   ${GREEN}cat README.md${NC}"
    echo ""
    echo -e "${RED}⚠️  Important Reminders:${NC}"
    echo -e "${YELLOW}   • Never commit your .env file with real credentials${NC}"
    echo -e "${YELLOW}   • Start with small position sizes for testing${NC}"
    echo -e "${YELLOW}   • Trading involves risk - only use funds you can afford to lose${NC}"
    echo -e "${YELLOW}   • Monitor your positions constantly${NC}"
    echo -e "${YELLOW}   • Keep sufficient USDC for hedging operations${NC}"
    echo ""
    echo -e "${GREEN}For help, run: ${NC}${BLUE}make help${NC}"
    echo ""
}

# Print troubleshooting tips
print_troubleshooting() {
    echo -e "${YELLOW}"
    echo "Troubleshooting Tips:"
    echo "────────────────────"
    echo ""
    echo "• Docker won't start:"
    echo "  - Restart Docker Desktop"
    echo "  - Check system resources (memory, disk space)"
    echo "  - Try: docker system prune -a"
    echo ""
    echo "• Permission errors:"
    echo "  - On Linux, add user to docker group: sudo usermod -aG docker \$USER"
    echo "  - Log out and back in"
    echo ""
    echo "• Port conflicts:"
    echo "  - Check if ports 3000, 8000, 6379 are available"
    echo "  - Stop conflicting services"
    echo "  - Edit docker-compose.yml to use different ports"
    echo ""
    echo "• Build failures:"
    echo "  - Clear Docker cache: docker builder prune"
    echo "  - Rebuild: make build"
    echo ""
    echo -e "${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting setup process...${NC}"
    echo ""

    # Run all checks
    check_docker
    check_docker_compose
    check_nodejs
    check_python

    echo ""
    show_system_info
    echo ""

    # Setup environment
    create_directories
    setup_env_file
    check_permissions

    # Test Docker
    test_docker

    # Pull images
    echo ""
    read -p "Pull Docker images now? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        pull_docker_images
    else
        echo -e "${YELLOW}Skipping image pull. Run 'docker-compose pull' later.${NC}"
    fi

    echo ""
    print_next_steps

    # Optional troubleshooting
    echo ""
    read -p "Show troubleshooting tips? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_troubleshooting
    fi

    echo -e "${GREEN}Setup script completed successfully!${NC}"
}

# Run main function
main
