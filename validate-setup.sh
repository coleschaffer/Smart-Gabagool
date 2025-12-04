#!/bin/bash
# Quick validation script to check all Docker setup files

echo "Validating Gabagool Docker Setup..."
echo ""

ERRORS=0

check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ $1 - MISSING"
        ERRORS=$((ERRORS + 1))
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo "✓ $1 (executable)"
    else
        echo "✗ $1 - NOT EXECUTABLE"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "Root Configuration Files:"
check_file "docker-compose.yml"
check_file "Makefile"
check_file ".env.example"
check_file ".gitignore"
check_file "README.md"
check_file "DOCKER_SETUP.md"
check_file "QUICKSTART.md"

echo ""
echo "Docker Configuration:"
check_file "backend/Dockerfile"
check_file "dashboard/Dockerfile"

echo ""
echo "Scripts:"
check_executable "scripts/setup.sh"
check_executable "scripts/start-dev.sh"

echo ""
echo "Validation of docker-compose.yml syntax:"
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ docker-compose.yml syntax is valid"
else
    echo "✗ docker-compose.yml has syntax errors"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ All files present and valid!"
    echo ""
    echo "Next steps:"
    echo "  1. cp .env.example .env"
    echo "  2. nano .env (add your credentials)"
    echo "  3. ./scripts/start-dev.sh"
else
    echo "❌ $ERRORS error(s) found"
    exit 1
fi
