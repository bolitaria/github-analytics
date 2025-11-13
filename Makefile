.PHONY: help install venv init up down clean test run-etl demo logs setup quick-start generate-sample-data check-env

# Colors for better output
GREEN := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RED := $(shell tput -Txterm setaf 1)
RESET := $(shell tput -Txterm sgr0)

.DEFAULT_GOAL := help

help:
	@echo "$(GREEN)🚀 GitHub Analytics Dashboard - Comandos disponibles:$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

check-env:
	@echo "$(GREEN)Verificando entorno...$(RESET)"
	@which python3 || (echo "$(RED)❌ Python3 no encontrado$(RESET)" && exit 1)
	@which docker || (echo "$(RED)❌ Docker no encontrado$(RESET)" && exit 1)
	@which docker-compose || (echo "$(RED)❌ Docker Compose no encontrado$(RESET)" && exit 1)
	@echo "$(GREEN)✅ Entorno verificado correctamente$(RESET)"

venv:
	@echo "$(GREEN)Creando entorno virtual...$(RESET)"
	python3 -m venv venv
	@echo "$(GREEN)✅ Entorno virtual creado en ./venv$(RESET)"
	@echo "$(YELLOW)Ejecuta: source venv/bin/activate$(RESET)"

install: check-env venv
	@echo "$(GREEN)Instalando dependencias...$(RESET)"
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencias instaladas$(RESET)"

up: check-env
	@echo "$(GREEN)Iniciando contenedores Docker...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✅ Contenedores iniciados$(RESET)"
	@echo "$(YELLOW)ClickHouse: http://localhost:8124$(RESET)"
	@echo "$(YELLOW)Grafana: http://localhost:3001 (admin/admin)$(RESET)"

down:
	@echo "$(YELLOW)Deteniendo contenedores...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✅ Contenedores detenidos$(RESET)"

init: up
	@echo "$(GREEN)Inicializando ClickHouse...$(RESET)"
	@sleep 10
	./venv/bin/python scripts/init_clickhouse.py
	@echo "$(GREEN)✅ Base de datos inicializada$(RESET)"

generate-sample-data: init
	@echo "$(GREEN)Generando datos de ejemplo...$(RESET)"
	./venv/bin/python scripts/generate_sample_data.py
	@echo "$(GREEN)✅ Datos de ejemplo generados$(RESET)"

run-etl:
	@echo "$(GREEN)Ejecutando ETL...$(RESET)"
	./venv/bin/python main.py
	@echo "$(GREEN)✅ ETL completado$(RESET)"

demo: generate-sample-data run-etl
	@echo "$(GREEN)🎉 Demostración completada!$(RESET)"
	@echo "$(YELLOW)Puedes ver los datos en:$(RESET)"
	@echo "$(YELLOW)  - ClickHouse: http://localhost:8124$(RESET)"
	@echo "$(YELLOW)  - Grafana: http://localhost:3001$(RESET)"

test:
	@echo "$(GREEN)Ejecutando tests...$(RESET)"
	./venv/bin/python -m pytest tests/ -v
	@echo "$(GREEN)✅ Tests completados$(RESET)"

logs:
	@echo "$(GREEN)Mostrando logs...$(RESET)"
	docker-compose logs -f

clean: down
	@echo "$(YELLOW)Limpiando contenedores y volúmenes...$(RESET)"
	docker-compose down -v
	@echo "$(GREEN)✅ Limpieza completada$(RESET)"

clean-all: clean
	@echo "$(YELLOW)Eliminando entorno virtual...$(RESET)"
	rm -rf venv
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf tests/__pycache__
	find . -name "*.pyc" -delete
	@echo "$(GREEN)✅ Limpieza completa realizada$(RESET)"

setup: check-env install init generate-sample-data
	@echo "$(GREEN)🎉 Configuración completada!$(RESET)"
	@echo ""
	@echo "$(YELLOW)Próximos pasos:$(RESET)"
	@echo "  1. make demo              # Para ejecutar demostración completa"
	@echo "  2. make logs              # Para ver logs"
	@echo ""
	@echo "$(YELLOW)URLs importantes:$(RESET)"
	@echo "  - ClickHouse: http://localhost:8124"
	@echo "  - Grafana: http://localhost:3001 (admin/admin)"

quick-start: setup demo
	@echo "$(GREEN)🚀 Inicio rápido completado!$(RESET)"

status:
	@echo "$(GREEN)Estado del sistema:$(RESET)"
	@docker-compose ps || echo "$(RED)❌ Docker no disponible$(RESET)"
	@echo ""
	@echo "$(YELLOW)Entorno virtual:$(RESET)"
	@if [ -d "venv" ]; then \
		echo "$(GREEN)✅ Entorno virtual presente$(RESET)"; \
	else \
		echo "$(RED)❌ Entorno virtual no encontrado$(RESET)"; \
	fi

info:
	@echo "$(GREEN)📊 GitHub Analytics Dashboard$(RESET)"
	@echo ""
	@echo "$(YELLOW)Descripción:$(RESET)"
	@echo "  Sistema de analytics en tiempo real usando ClickHouse"
	@echo "  y GitHub API para análisis de repositorios"
	@echo ""
	@echo "$(YELLOW)Tecnologías:$(RESET)"
	@echo "  - Python 3 + TypeScript patterns"
	@echo "  - ClickHouse (base de datos columnar)"
	@echo "  - Docker + Docker Compose"
	@echo "  - Grafana (visualización)"