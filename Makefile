.PHONY: help install venv init up down clean test run-etl demo logs setup quick-start generate-sample-data check-env venv-check venv-fix restart status activate info health-check logs-clickhouse logs-grafana init-users export-bigquery run-scheduler setup-grafana test-integration deploy-gcp train-model update-thresholds generate-dashboard deploy-dashboard enterprise-deploy lint pre-push

# Colors for better output
GREEN := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RED := $(shell tput -Txterm setaf 1)
BLUE := $(shell tput -Txterm setaf 4)
MAGENTA := $(shell tput -Txterm setaf 5)
RESET := $(shell tput -Txterm sgr0)

.DEFAULT_GOAL := help

help:
	@echo "$(GREEN)🚀 GitHub Analytics Dashboard - Available commands:$(RESET)"
	@echo ""
	@echo "$(BLUE)📦 SETUP & CONFIGURATION:$(RESET)"
	@echo "  $(YELLOW)setup$(RESET)           - Complete project setup"
	@echo "  $(YELLOW)quick-start$(RESET)     - Quick start (setup + demo)"
	@echo "  $(YELLOW)check-env$(RESET)       - Check system requirements"
	@echo "  $(YELLOW)venv$(RESET)            - Create virtual environment"
	@echo "  $(YELLOW)venv-check$(RESET)      - Check virtual environment status"
	@echo "  $(YELLOW)venv-fix$(RESET)        - Repair corrupted virtual environment"
	@echo "  $(YELLOW)install$(RESET)         - Install Python dependencies"
	@echo ""
	@echo "$(BLUE)🐳 DOCKER SERVICES:$(RESET)"
	@echo "  $(YELLOW)up$(RESET)              - Start containers (ClickHouse + Grafana)"
	@echo "  $(YELLOW)down$(RESET)            - Stop containers"
	@echo "  $(YELLOW)restart$(RESET)         - Restart containers"
	@echo "  $(YELLOW)logs$(RESET)            - Show logs of all services"
	@echo "  $(YELLOW)logs-clickhouse$(RESET) - Show only ClickHouse logs"
	@echo "  $(YELLOW)logs-grafana$(RESET)    - Show only Grafana logs"
	@echo ""
	@echo "$(BLUE)📊 DATA & ETL:$(RESET)"
	@echo "  $(YELLOW)init$(RESET)            - Initialize database"
	@echo "  $(YELLOW)generate-sample-data$(RESET) - Generate sample data"
	@echo "  $(YELLOW)run-etl$(RESET)         - Run complete ETL process"
	@echo "  $(YELLOW)demo$(RESET)            - Run full demonstration"
	@echo ""
	@echo "$(BLUE)🤖 AUTOMATION & MODELS:$(RESET)"
	@echo "  $(YELLOW)init-users$(RESET)      - Create admin user for authentication"
	@echo "  $(YELLOW)run-scheduler$(RESET)   - Start scheduler (cron-like tasks)"
	@echo "  $(YELLOW)train-model$(RESET)     - Train issue classifier model"
	@echo ""
	@echo "$(BLUE)🧪 TESTING & DEVELOPMENT:$(RESET)"
	@echo "  $(YELLOW)test$(RESET)            - Run unit tests"
	@echo "  $(YELLOW)test-integration$(RESET)- Run integration tests"
	@echo "  $(YELLOW)lint$(RESET)            - Run linters (black, isort, flake8)"
	@echo "  $(YELLOW)pre-push$(RESET)        - Run all checks before push (lint + test + test-integration)"
	@echo "  $(YELLOW)status$(RESET)          - Check system status"
	@echo "  $(YELLOW)health-check$(RESET)    - Check service health"
	@echo "  $(YELLOW)activate$(RESET)        - Show command to activate venv"
	@echo ""
	@echo "$(BLUE)☁️ GCP INTEGRATION:$(RESET)"
	@echo "  $(YELLOW)export-bigquery$(RESET) - Export data to BigQuery"
	@echo "  $(YELLOW)setup-grafana$(RESET)   - Automatically configure Grafana dashboards"
	@echo "  $(YELLOW)deploy-gcp$(RESET)      - Deploy API to Google Cloud Run"
	@echo ""
	@echo "$(BLUE)🧹 CLEANUP:$(RESET)"
	@echo "  $(YELLOW)clean$(RESET)           - Clean containers and volumes"
	@echo "  $(YELLOW)clean-all$(RESET)       - Full cleanup + virtual environment"
	@echo ""
	@echo "$(BLUE)📚 INFORMATION:$(RESET)"
	@echo "  $(YELLOW)info$(RESET)            - Show project information"
	@echo "  $(YELLOW)help$(RESET)            - Show this help"
	@echo ""
	@echo "$(MAGENTA)💡 Important URLs:$(RESET)"
	@echo "  ClickHouse: http://localhost:8124"
	@echo "  Grafana:    http://localhost:3001 (admin/admin)"
	@echo "  Flask API:  http://localhost:8001 (authentication required)"
	@echo ""
	@echo "$(MAGENTA)🚀 Recommended flow:$(RESET)"
	@echo "  make setup           # Initial setup"
	@echo "  make init-users      # Create admin user"
	@echo "  make run-etl         # Fetch real data (set GITHUB_TOKEN first)"
	@echo "  make train-model     # Train issue classifier"
	@echo "  make run-scheduler   # Automate periodic tasks"
	@echo "  make setup-grafana   # Visualize data"

check-env:
	@echo "$(GREEN)Checking environment...$(RESET)"
	@which python3 || (echo "$(RED)❌ Python3 not found$(RESET)" && exit 1)
	@which docker || (echo "$(RED)❌ Docker not found$(RESET)" && exit 1)
	@which docker-compose || (echo "$(RED)❌ Docker Compose not found$(RESET)" && exit 1)
	@echo "$(GREEN)✅ Environment verified$(RESET)"

venv-check:
	@echo "$(GREEN)Checking virtual environment...$(RESET)"
	@if [ -d "venv" ]; then \
		if [ -f "venv/bin/python" ] || [ -f "venv/bin/python3" ]; then \
			echo "$(GREEN)✅ Virtual environment exists and has Python$(RESET)"; \
		else \
			echo "$(YELLOW)⚠️  Virtual environment exists but has no Python, recreating...$(RESET)"; \
			$(MAKE) venv-fix; \
		fi \
	else \
		echo "$(YELLOW)⚠️  Virtual environment not found, creating...$(RESET)"; \
		$(MAKE) venv; \
	fi

venv-fix:
	@echo "$(GREEN)Fixing virtual environment issues...$(RESET)"
	@if [ -d "venv" ]; then \
		echo "$(YELLOW)Removing corrupted virtual environment...$(RESET)"; \
		rm -rf venv; \
	fi
	@$(MAKE) venv

venv:
	@echo "$(GREEN)Creating virtual environment...$(RESET)"
	@python3 -m venv venv
	@if [ -f "venv/bin/python" ] || [ -f "venv/bin/python3" ]; then \
		echo "$(GREEN)✅ Virtual environment created successfully in ./venv$(RESET)"; \
	else \
		echo "$(RED)❌ Error: Could not create virtual environment$(RESET)"; \
		echo "$(YELLOW)Trying with python3 explicitly...$(RESET)"; \
		python3 -m venv venv --copies; \
		if [ -f "venv/bin/python3" ]; then \
			echo "$(GREEN)✅ Virtual environment created with python3$(RESET)"; \
		else \
			echo "$(RED)❌ Critical error: Cannot create virtual environment$(RESET)"; \
			echo "$(YELLOW)Please check your Python installation:$(RESET)"; \
			echo "$(YELLOW)  - python3 --version$(RESET)"; \
			echo "$(YELLOW)  - which python3$(RESET)"; \
			exit 1; \
		fi \
	fi
	@echo "$(YELLOW)Run: source venv/bin/activate$(RESET)"

install: check-env venv-check
	@echo "$(GREEN)Installing dependencies...$(RESET)"
	@if [ -f "venv/bin/python" ] || [ -f "venv/bin/python3" ]; then \
		if [ -f "venv/bin/python" ]; then \
			echo "$(YELLOW)Using venv/bin/python$(RESET)"; \
			./venv/bin/python -m pip install --upgrade pip || (echo "$(RED)❌ Error upgrading pip$(RESET)" && exit 1); \
			./venv/bin/python -m pip install -r requirements.txt || (echo "$(RED)❌ Error installing dependencies$(RESET)" && exit 1); \
			./venv/bin/python -m pip install black isort flake8 || (echo "$(RED)❌ Error installing linting tools$(RESET)" && exit 1); \
		else \
			echo "$(YELLOW)Using venv/bin/python3$(RESET)"; \
			./venv/bin/python3 -m pip install --upgrade pip || (echo "$(RED)❌ Error upgrading pip$(RESET)" && exit 1); \
			./venv/bin/python3 -m pip install -r requirements.txt || (echo "$(RED)❌ Error installing dependencies$(RESET)" && exit 1); \
			./venv/bin/python3 -m pip install black isort flake8 || (echo "$(RED)❌ Error installing linting tools$(RESET)" && exit 1); \
		fi \
	else \
		echo "$(RED)❌ Cannot find Python in virtual environment$(RESET)"; \
		echo "$(YELLOW)Attempting to repair virtual environment...$(RESET)"; \
		$(MAKE) venv-fix; \
		echo "$(YELLOW)Retrying installation...$(RESET)"; \
		if [ -f "venv/bin/python" ]; then \
			./venv/bin/python -m pip install --upgrade pip; \
			./venv/bin/python -m pip install -r requirements.txt; \
			./venv/bin/python -m pip install black isort flake8; \
		else \
			./venv/bin/python3 -m pip install --upgrade pip; \
			./venv/bin/python3 -m pip install -r requirements.txt; \
			./venv/bin/python3 -m pip install black isort flake8; \
		fi \
	fi
	@echo "$(GREEN)✅ Dependencies installed successfully$(RESET)"

up: check-env
	@echo "$(GREEN)Starting Docker containers...$(RESET)"
	@if docker-compose ps | grep -q "Up"; then \
		echo "$(YELLOW)⚠️  Some containers are already running. Use 'make restart' if needed.$(RESET)"; \
		docker-compose ps; \
	else \
		docker-compose up -d; \
		echo "$(GREEN)✅ Containers started$(RESET)"; \
		echo "$(YELLOW)ClickHouse: http://localhost:8124$(RESET)"; \
		echo "$(YELLOW)Grafana: http://localhost:3001 (admin/admin)$(RESET)"; \
	fi

down:
	@echo "$(YELLOW)Stopping containers...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✅ Containers stopped$(RESET)"

restart: down up
	@echo "$(GREEN)✅ Containers restarted$(RESET)"

init: up
	@echo "$(GREEN)Initializing ClickHouse...$(RESET)"
	@sleep 15
	@if [ -f "venv/bin/python" ]; then \
		PYTHONPATH=$(PWD) ./venv/bin/python scripts/init_clickhouse.py; \
	elif [ -f "venv/bin/python3" ]; then \
		PYTHONPATH=$(PWD) ./venv/bin/python3 scripts/init_clickhouse.py; \
	else \
		echo "$(RED)❌ Cannot run Python from virtual environment$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Database initialized$(RESET)"

generate-sample-data: init
	@echo "$(GREEN)Generating sample data...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/generate_sample_data.py; \
	else \
		./venv/bin/python3 scripts/generate_sample_data.py; \
	fi
	@echo "$(GREEN)✅ Sample data generated$(RESET)"

run-etl:
	@echo "$(GREEN)Running ETL...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python main.py; \
	else \
		./venv/bin/python3 main.py; \
	fi
	@echo "$(GREEN)✅ ETL completed$(RESET)"

demo: generate-sample-data run-etl
	@echo "$(GREEN)🎉 Demonstration completed!$(RESET)"
	@echo "$(YELLOW)You can view data at:$(RESET)"
	@echo "$(YELLOW)  - ClickHouse: http://localhost:8124$(RESET)"
	@echo "$(YELLOW)  - Grafana: http://localhost:3001$(RESET)"

test:
	@echo "$(GREEN)Running tests...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python -m pytest tests/ -v --ignore=tests/integration; \
	else \
		./venv/bin/python3 -m pytest tests/ -v --ignore=tests/integration; \
	fi
	@echo "$(GREEN)✅ Tests completed$(RESET)"

test-integration:
	@echo "$(GREEN)Running integration tests...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python -m pytest tests/test_integration.py -v; \
	else \
		./venv/bin/python3 -m pytest tests/test_integration.py -v; \
	fi

lint:
	@echo "$(GREEN)Running linters...$(RESET)"
	@# Ensure linting tools are installed
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python -m pip install black isort flake8 --quiet; \
		./venv/bin/python -m black --check src/ tests/ || (echo "$(RED)❌ Black formatting check failed$(RESET)" && exit 1); \
		./venv/bin/python -m isort --check-only src/ tests/ || (echo "$(RED)❌ Isort check failed$(RESET)" && exit 1); \
		./venv/bin/python -m flake8 src/ tests/ --max-line-length=120 || (echo "$(RED)❌ Flake8 check failed$(RESET)" && exit 1); \
	else \
		./venv/bin/python3 -m pip install black isort flake8 --quiet; \
		./venv/bin/python3 -m black --check src/ tests/ || (echo "$(RED)❌ Black formatting check failed$(RESET)" && exit 1); \
		./venv/bin/python3 -m isort --check-only src/ tests/ || (echo "$(RED)❌ Isort check failed$(RESET)" && exit 1); \
		./venv/bin/python3 -m flake8 src/ tests/ --max-line-length=120 || (echo "$(RED)❌ Flake8 check failed$(RESET)" && exit 1); \
	fi
	@echo "$(GREEN)✅ Linting passed$(RESET)"

pre-push: lint test test-integration
	@echo "$(GREEN)✅ All pre-push checks passed! You can now push safely.$(RESET)"

logs:
	@echo "$(GREEN)Showing logs...$(RESET)"
	docker-compose logs -f

logs-clickhouse:
	@echo "$(GREEN)Showing ClickHouse logs...$(RESET)"
	docker-compose logs clickhouse -f

logs-grafana:
	@echo "$(GREEN)Showing Grafana logs...$(RESET)"
	docker-compose logs grafana -f

clean: down
	@echo "$(YELLOW)Cleaning containers and volumes...$(RESET)"
	docker-compose down -v
	@echo "$(GREEN)✅ Cleanup completed$(RESET)"

clean-all: clean
	@echo "$(YELLOW)Removing virtual environment...$(RESET)"
	rm -rf venv
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf tests/__pycache__
	find . -name "*.pyc" -delete
	@echo "$(GREEN)✅ Full cleanup completed$(RESET)"

setup: check-env install init generate-sample-data
	@echo "$(GREEN)🎉 Setup completed!$(RESET)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "  1. make init-users      # Create admin user for authentication"
	@echo "  2. make run-etl         # Fetch real data (set GITHUB_TOKEN in .env)"
	@echo "  3. make train-model     # Train issue classifier"
	@echo "  4. make run-scheduler   # Automate periodic tasks"
	@echo ""
	@echo "$(YELLOW)Important URLs:$(RESET)"
	@echo "  - ClickHouse: http://localhost:8124"
	@echo "  - Grafana: http://localhost:3001 (admin/admin)"
	@echo "  - API: http://localhost:8001 (after running python run.py)"

quick-start: setup demo
	@echo "$(GREEN)🚀 Quick start completed!$(RESET)"

status:
	@echo "$(GREEN)System status:$(RESET)"
	@docker-compose ps || echo "$(RED)❌ Docker not available$(RESET)"
	@echo ""
	@echo "$(YELLOW)Virtual environment:$(RESET)"
	@if [ -d "venv" ]; then \
		if [ -f "venv/bin/python" ] || [ -f "venv/bin/python3" ]; then \
			echo "$(GREEN)✅ Virtual environment present and functional$(RESET)"; \
			if [ -f "venv/bin/python" ]; then \
				./venv/bin/python --version | xargs echo "  Python version: "; \
			else \
				./venv/bin/python3 --version | xargs echo "  Python version: "; \
			fi \
		else \
			echo "$(RED)❌ Virtual environment corrupted$(RESET)"; \
		fi \
	else \
		echo "$(RED)❌ Virtual environment not found$(RESET)"; \
	fi

init-users:
	@echo "$(GREEN)Initializing users...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/init_users.py; \
	else \
		./venv/bin/python3 scripts/init_users.py; \
	fi

export-bigquery:
	@echo "$(GREEN)Exporting data to BigQuery...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/export_to_bigquery.py; \
	else \
		./venv/bin/python3 scripts/export_to_bigquery.py; \
	fi

run-scheduler:
	@echo "$(GREEN)Starting scheduler...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/scheduler.py; \
	else \
		./venv/bin/python3 scripts/scheduler.py; \
	fi

setup-grafana:
	@echo "$(GREEN)Configuring Grafana automatically...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/setup_grafana.py; \
	else \
		./venv/bin/python3 scripts/setup_grafana.py; \
	fi

deploy-gcp:
	@echo "$(GREEN)Deploying to Google Cloud Run...$(RESET)"
	./scripts/deploy_gcp.sh

train-model:
	@echo "$(GREEN)Training issue classifier model...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/train_issue_classifier.py; \
	else \
		./venv/bin/python3 scripts/train_issue_classifier.py; \
	fi

update-thresholds:
	@echo "$(GREEN)Updating dynamic thresholds...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/anomaly_detection.py; \
	else \
		./venv/bin/python3 scripts/anomaly_detection.py; \
	fi

generate-dashboard:
	@echo "$(GREEN)Generating enterprise dashboard JSON...$(RESET)"
	mkdir -p grafana/dashboards
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/generate_dashboard.py > grafana/dashboards/enterprise.json; \
	else \
		./venv/bin/python3 scripts/generate_dashboard.py > grafana/dashboards/enterprise.json; \
	fi

deploy-dashboard: generate-dashboard
	@echo "$(GREEN)Deploying dashboard to Grafana...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/deploy_dashboard.py grafana/dashboards/enterprise.json; \
	else \
		./venv/bin/python3 scripts/deploy_dashboard.py grafana/dashboards/enterprise.json; \
	fi

enterprise-deploy: update-thresholds generate-dashboard deploy-dashboard
	@echo "$(GREEN)✅ Enterprise dashboard deployed!$(RESET)"

# Additional targets from original (kept for compatibility)
.PHONY: generate-full-dashboard deploy-full-dashboard full-enterprise-deploy

generate-full-dashboard:
	@echo "$(GREEN)Generating full enterprise dashboard...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/generate_full_dashboard.py; \
	else \
		./venv/bin/python3 scripts/generate_full_dashboard.py; \
	fi

deploy-full-dashboard:
	@echo "$(GREEN)Deploying full enterprise dashboard...$(RESET)"
	@if [ -f "venv/bin/python" ]; then \
		./venv/bin/python scripts/generate_full_dashboard.py; \
	else \
		./venv/bin/python3 scripts/generate_full_dashboard.py; \
	fi

full-enterprise-deploy: update-thresholds generate-full-dashboard
	@echo "$(GREEN)✅ Full enterprise dashboard deployed!$(RESET)"

info:
	@echo "$(GREEN)📊 GitHub Analytics Dashboard$(RESET)"
	@echo ""
	@echo "$(YELLOW)Description:$(RESET)"
	@echo "  Real-time analytics system for GitHub repositories using ClickHouse"
	@echo ""
	@echo "$(YELLOW)Technologies:$(RESET)"
	@echo "  - Python 3.12"
	@echo "  - ClickHouse (columnar database)"
	@echo "  - Docker & Docker Compose"
	@echo "  - Grafana (visualization)"
	@echo "  - Flask API with JWT authentication"
	@echo "  - scikit-learn (ML classification)"
	@echo "  - Prophet (time series forecasting)"
	@echo "  - Google Cloud Platform (BigQuery, Cloud Run)"

activate:
	@echo "$(GREEN)Activating virtual environment...$(RESET)"
	@if [ -f "venv/bin/activate" ]; then \
		echo "$(YELLOW)Run: source venv/bin/activate$(RESET)"; \
	else \
		echo "$(RED)❌ Activation script not found$(RESET)"; \
		$(MAKE) venv-fix; \
	fi

health-check:
	@echo "$(GREEN)Checking service health...$(RESET)"
	@echo "$(YELLOW)ClickHouse:$(RESET)"
	@curl -f http://localhost:8124/ping > /dev/null 2>&1 && echo "$(GREEN)✅ ClickHouse is responding$(RESET)" || echo "$(RED)❌ ClickHouse is not responding$(RESET)"
	@echo "$(YELLOW)Grafana:$(RESET)"
	@curl -f http://localhost:3001/api/health > /dev/null 2>&1 && echo "$(GREEN)✅ Grafana is responding$(RESET)" || echo "$(RED)❌ Grafana is not responding$(RESET)"
	@echo "$(YELLOW)API:$(RESET)"
	@curl -f http://localhost:8001/api/health > /dev/null 2>&1 && echo "$(GREEN)✅ API is responding$(RESET)" || echo "$(YELLOW)⚠️  API may not be running (start with 'python run.py')$(RESET)"