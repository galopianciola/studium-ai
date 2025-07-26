# Studium Backend - Docker-First Makefile
# AI-powered educational content generation for Spanish-speaking students

.PHONY: help build dev prod stop clean logs shell test

# Default target
help: ## Show this help message
	@echo "🎓 Studium Backend - Docker Commands"
	@echo "==================================="
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Environment variables
PROJECT_NAME := studium
IMAGE_NAME := $(PROJECT_NAME):latest
DEV_CONTAINER := $(PROJECT_NAME)-dev
PROD_CONTAINER := $(PROJECT_NAME)-prod

# =============================================================================
# Development Commands (Docker-based)
# =============================================================================

build: ## Build Docker image for development
	@echo "🔨 Building Docker image..."
	docker build -t $(IMAGE_NAME) .

dev: ## Start development server with hot reload (Docker)
	@echo "🔧 Starting development server with Docker..."
	@make stop-dev 2>/dev/null || true
	docker run -it --rm \
		--name $(DEV_CONTAINER) \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD):/app \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/vector_store:/app/vector_store \
		$(IMAGE_NAME) \
		python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
	@echo "🎉 Development server started at http://localhost:8000"

dev-bg: ## Start development server in background
	@echo "🔧 Starting development server in background..."
	@make stop-dev 2>/dev/null || true
	docker run -d \
		--name $(DEV_CONTAINER) \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD):/app \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/vector_store:/app/vector_store \
		$(IMAGE_NAME) \
		python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
	@echo "✅ Development server running at http://localhost:8000"

stop-dev: ## Stop development container
	@echo "🛑 Stopping development container..."
	@docker stop $(DEV_CONTAINER) 2>/dev/null || true
	@docker rm $(DEV_CONTAINER) 2>/dev/null || true

# =============================================================================
# Production Commands
# =============================================================================

prod: ## Start production server
	@echo "🚀 Starting production server..."
	@make stop-prod 2>/dev/null || true
	docker run -d \
		--name $(PROD_CONTAINER) \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/vector_store:/app/vector_store \
		--restart unless-stopped \
		$(IMAGE_NAME)
	@echo "✅ Production server running at http://localhost:8000"

stop-prod: ## Stop production container
	@echo "🛑 Stopping production container..."
	@docker stop $(PROD_CONTAINER) 2>/dev/null || true
	@docker rm $(PROD_CONTAINER) 2>/dev/null || true

# =============================================================================
# Docker Compose Commands
# =============================================================================

up: ## Start all services with docker-compose
	@echo "🐳 Starting all services..."
	docker-compose up -d
	@echo "✅ Services started at http://localhost:8000"

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	docker-compose down

logs-compose: ## Show docker-compose logs
	docker-compose logs -f

# =============================================================================
# Development Tools (Docker-based)
# =============================================================================

shell: ## Open shell in development container
	@echo "🐚 Opening shell in development container..."
	@if [ $$(docker ps -q -f name=$(DEV_CONTAINER)) ]; then \
		docker exec -it $(DEV_CONTAINER) /bin/bash; \
	else \
		echo "Starting temporary container for shell access..."; \
		docker run -it --rm \
			--env-file .env \
			-v $(PWD):/app \
			$(IMAGE_NAME) /bin/bash; \
	fi

test: ## Run tests in Docker
	@echo "🧪 Running tests in Docker..."
	docker run --rm \
		--env-file .env \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		pytest tests/ -v

test-spanish: ## Test Spanish AI content generation
	@echo "🇪🇸 Testing Spanish AI generation..."
	docker run --rm \
		--env-file .env \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		python test_spanish_ai.py

lint: ## Run code linting in Docker
	@echo "🔍 Running linting checks..."
	docker run --rm \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		sh -c "pip install flake8 && flake8 app/ --max-line-length=100 --ignore=E203,W503"

format: ## Format code with black in Docker
	@echo "🎨 Formatting code..."
	docker run --rm \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		sh -c "pip install black && black app/ --line-length=100"

freeze: ## Freeze current package versions to requirements-frozen.txt
	@echo "🧊 Freezing package versions..."
	docker run --rm \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		pip freeze > requirements-frozen.txt
	@echo "✅ Frozen requirements saved to requirements-frozen.txt"
	@echo "💡 Use 'cp requirements-frozen.txt requirements.txt' to pin versions"

# =============================================================================
# Monitoring and Debugging
# =============================================================================

logs: ## Show development container logs
	@if [ $$(docker ps -q -f name=$(DEV_CONTAINER)) ]; then \
		echo "📋 Development container logs:"; \
		docker logs -f $(DEV_CONTAINER); \
	elif [ $$(docker ps -q -f name=$(PROD_CONTAINER)) ]; then \
		echo "📋 Production container logs:"; \
		docker logs -f $(PROD_CONTAINER); \
	else \
		echo "❌ No containers running"; \
	fi

logs-dev: ## Show development container logs
	docker logs -f $(DEV_CONTAINER)

logs-prod: ## Show production container logs
	docker logs -f $(PROD_CONTAINER)

stats: ## Show container resource usage
	@echo "📊 Container statistics:"
	@if [ $$(docker ps -q -f name=$(DEV_CONTAINER)) ]; then \
		docker stats $(DEV_CONTAINER) --no-stream; \
	elif [ $$(docker ps -q -f name=$(PROD_CONTAINER)) ]; then \
		docker stats $(PROD_CONTAINER) --no-stream; \
	else \
		echo "❌ No containers running"; \
	fi

health: ## Check API health
	@echo "🏥 Checking API health..."
	@curl -s http://localhost:8000/health || echo "❌ API not responding"

ai-status: ## Check AI services status
	@echo "🤖 Checking AI services status..."
	@curl -s http://localhost:8000/api/v1/ai-status || echo "❌ API not responding"

# =============================================================================
# Cleanup Commands
# =============================================================================

stop: ## Stop all containers
	@echo "🛑 Stopping all containers..."
	@make stop-dev 2>/dev/null || true
	@make stop-prod 2>/dev/null || true

clean: ## Clean up containers and images
	@echo "🧹 Cleaning up Docker resources..."
	@make stop
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@docker system prune -f

clean-data: ## Clean application data directories
	@echo "🗂️ Cleaning application data..."
	rm -rf uploads/* logs/* vector_store/*
	mkdir -p uploads logs vector_store

clean-all: clean clean-data ## Deep clean everything
	@echo "🧹 Deep cleaning all Docker resources..."
	@docker system prune -af
	@docker volume prune -f

# =============================================================================
# Setup and Configuration
# =============================================================================

setup: ## Initialize project for Docker development
	@echo "🚀 Setting up Studium for Docker development..."
	@if [ ! -f .env ]; then \
		echo "📋 Creating .env file..."; \
		cp .env.example .env; \
		echo "✅ .env created. Please add your API keys!"; \
	else \
		echo "✅ .env file exists"; \
	fi
	@mkdir -p uploads logs vector_store
	@echo "📁 Created data directories"
	@echo ""
	@echo "🎯 Next steps:"
	@echo "1. Edit .env with your ANTHROPIC_API_KEY"
	@echo "2. Run: make build"
	@echo "3. Run: make dev (for development)"
	@echo "4. Visit: http://localhost:8000/docs"

rebuild: ## Rebuild image and restart development
	@echo "🔄 Rebuilding and restarting..."
	@make stop
	@make build
	@make dev-bg

# =============================================================================
# Hackathon Quick Commands
# =============================================================================

hackathon: ## Complete hackathon setup and start
	@echo "🏆 Hackathon quick setup..."
	@make setup
	@make build
	@make dev-bg
	@sleep 3
	@make health
	@make ai-status
	@echo ""
	@echo "🎉 Studium ready for hackathon!"
	@echo "📖 Docs: http://localhost:8000/docs"
	@echo "🔧 Logs: make logs"
	@echo "🧪 Test: make test-spanish"

demo: ## Start demo mode (production-like)
	@echo "🎬 Starting demo mode..."
	@make stop
	@make prod
	@sleep 3
	@make health
	@echo "🎉 Demo ready at http://localhost:8000"

# =============================================================================
# Utility Commands
# =============================================================================

ps: ## Show running containers
	@echo "📋 Running containers:"
	@docker ps --filter "name=$(PROJECT_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

images: ## Show project images
	@echo "🖼️ Project images:"
	@docker images | grep $(PROJECT_NAME) || echo "No images found"

env-check: ## Validate environment setup
	@echo "🔧 Environment Check"
	@echo "==================="
	@echo "Docker: $$(docker --version 2>/dev/null || echo '❌ Not installed')"
	@echo "Docker Compose: $$(docker-compose --version 2>/dev/null || echo '❌ Not installed')"
	@echo ""
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		if grep -q "your_anthropic_api_key_here" .env; then \
			echo "❌ ANTHROPIC_API_KEY not configured"; \
		else \
			echo "✅ ANTHROPIC_API_KEY configured"; \
		fi; \
		if grep -q "your_openai_api_key_here" .env; then \
			echo "⚠️  OPENAI_API_KEY not configured (optional)"; \
		else \
			echo "✅ OPENAI_API_KEY configured"; \
		fi; \
	else \
		echo "❌ .env file missing - run: make setup"; \
	fi

info: ## Show project information
	@echo "🎓 Studium Backend - Docker Development"
	@echo "======================================"
	@echo "AI Model: Claude Sonnet 4 (claude-sonnet-4-20250514)"
	@echo "Language: Spanish-optimized educational content"
	@echo "Development: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Health: http://localhost:8000/health"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  Development: make dev"
	@echo "  Production: make prod"
	@echo "  Testing: make test-spanish"
	@echo "  Shell: make shell"