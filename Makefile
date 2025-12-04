.PHONY: help dev backend dashboard redis logs logs-backend logs-dashboard clean reset build test shell-backend shell-dashboard stop restart

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Gabagool - Polymarket Volatility Arbitrage Bot$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-18s$(NC) %s\n", $$1, $$2}'

dev: ## Start all services in development mode
	@echo "$(GREEN)Starting Gabagool in development mode...$(NC)"
	@docker-compose up --build

dev-d: ## Start all services in background (detached mode)
	@echo "$(GREEN)Starting Gabagool in background...$(NC)"
	@docker-compose up -d --build
	@echo "$(GREEN)Services started! Dashboard: http://localhost:3000$(NC)"
	@echo "$(GREEN)API Docs: http://localhost:8000/docs$(NC)"

backend: ## Start only backend service
	@echo "$(GREEN)Starting backend service...$(NC)"
	@docker-compose up backend redis

dashboard: ## Start only dashboard service
	@echo "$(GREEN)Starting dashboard service...$(NC)"
	@docker-compose up dashboard backend redis

redis: ## Start only Redis service
	@echo "$(GREEN)Starting Redis service...$(NC)"
	@docker-compose up redis

logs: ## View logs from all services
	@docker-compose logs -f

logs-backend: ## View backend logs only
	@docker-compose logs -f backend

logs-dashboard: ## View dashboard logs only
	@docker-compose logs -f dashboard

logs-redis: ## View Redis logs only
	@docker-compose logs -f redis

stop: ## Stop all services
	@echo "$(RED)Stopping all services...$(NC)"
	@docker-compose stop

restart: ## Restart all services
	@echo "$(GREEN)Restarting all services...$(NC)"
	@docker-compose restart

clean: ## Stop and remove all containers
	@echo "$(RED)Stopping and removing containers...$(NC)"
	@docker-compose down

reset: ## Clean and remove volumes (WARNING: deletes data)
	@echo "$(RED)WARNING: This will delete all data including Redis cache!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)Reset complete!$(NC)"; \
	else \
		echo "$(BLUE)Reset cancelled.$(NC)"; \
	fi

build: ## Rebuild all Docker images
	@echo "$(GREEN)Rebuilding all images...$(NC)"
	@docker-compose build --no-cache

build-backend: ## Rebuild backend image only
	@echo "$(GREEN)Rebuilding backend image...$(NC)"
	@docker-compose build --no-cache backend

build-dashboard: ## Rebuild dashboard image only
	@echo "$(GREEN)Rebuilding dashboard image...$(NC)"
	@docker-compose build --no-cache dashboard

test: ## Run test suite
	@echo "$(GREEN)Running tests...$(NC)"
	@docker-compose run --rm backend pytest -v

test-backend: ## Run backend tests only
	@echo "$(GREEN)Running backend tests...$(NC)"
	@docker-compose run --rm backend pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@docker-compose run --rm backend pytest --cov=. --cov-report=html --cov-report=term

shell-backend: ## Open shell in backend container
	@docker-compose exec backend /bin/bash

shell-dashboard: ## Open shell in dashboard container
	@docker-compose exec dashboard /bin/sh

shell-redis: ## Open Redis CLI
	@docker-compose exec redis redis-cli

ps: ## Show status of all services
	@docker-compose ps

stats: ## Show container resource usage
	@docker stats gabagool-backend gabagool-dashboard gabagool-redis

check-env: ## Check if .env file exists and is configured
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(NC)"; \
		echo "$(BLUE)Run: cp .env.example .env$(NC)"; \
		echo "$(BLUE)Then edit .env with your credentials$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN).env file found!$(NC)"; \
		if grep -q "your_api_key_here" .env; then \
			echo "$(RED)Warning: .env contains placeholder values!$(NC)"; \
			echo "$(BLUE)Edit .env with your real credentials$(NC)"; \
		else \
			echo "$(GREEN).env appears to be configured$(NC)"; \
		fi \
	fi

setup: ## Initial setup - create .env and pull images
	@echo "$(GREEN)Running initial setup...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN).env created from template$(NC)"; \
		echo "$(BLUE)Edit .env with your credentials before starting$(NC)"; \
	else \
		echo "$(BLUE).env already exists$(NC)"; \
	fi
	@docker-compose pull
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Edit .env with your Polymarket credentials"
	@echo "  2. Run: make dev"

lint-backend: ## Lint backend code
	@echo "$(GREEN)Linting backend code...$(NC)"
	@docker-compose run --rm backend flake8 .
	@docker-compose run --rm backend black --check .

format-backend: ## Format backend code
	@echo "$(GREEN)Formatting backend code...$(NC)"
	@docker-compose run --rm backend black .

lint-dashboard: ## Lint dashboard code
	@echo "$(GREEN)Linting dashboard code...$(NC)"
	@docker-compose run --rm dashboard npm run lint

prune: ## Remove unused Docker resources
	@echo "$(RED)Removing unused Docker resources...$(NC)"
	@docker system prune -f

backup-redis: ## Backup Redis data
	@echo "$(GREEN)Backing up Redis data...$(NC)"
	@docker-compose exec redis redis-cli BGSAVE
	@echo "$(GREEN)Backup initiated$(NC)"

open-dashboard: ## Open dashboard in browser
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Open http://localhost:3000 in your browser"

open-api-docs: ## Open API documentation in browser
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"
