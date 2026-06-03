# 📋 GitHub Analytics Dashboard - Runbook Operativo

**Versión:** 1.0  
**Última actualización:** Junio 2026  
**Autores:** Equipo DevOps

---

## 📑 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Requisitos Previos](#requisitos-previos)
4. [Instalación y Setup Inicial](#instalación-y-setup-inicial)
5. [Configuración](#configuración)
6. [Operaciones Diarias](#operaciones-diarias)
7. [Mantenimiento](#mantenimiento)
8. [Solución de Problemas](#solución-de-problemas)
9. [Backup y Recuperación](#backup-y-recuperación)
10. [Escalabilidad](#escalabilidad)
11. [Seguridad](#seguridad)
12. [Monitoreo y Alertas](#monitoreo-y-alertas)
13. [Procedimientos de Respuesta a Incidentes](#procedimientos-de-respuesta-a-incidentes)

---

## 🎯 Visión General

### ¿Qué es GitHub Analytics Dashboard?

Un sistema en tiempo real de análisis de actividad en repositorios de GitHub que:
- **Captura eventos** desde GitHub API (commits, PRs, issues)
- **Almacena datos** en ClickHouse para análisis rápido
- **Predice tendencias** usando modelos ML (Prophet para forecasting)
- **Clasifica issues** automáticamente (bug, feature, doc, etc.)
- **Visualiza datos** en dashboards Grafana interactivos
- **Proporciona API REST** con autenticación JWT

### Caso de uso principal

Monitorear y analizar la salud, actividad y tendencias de repositorios GitHub a través de dashboards ejecutivos.

### Stack tecnológico

| Componente | Tecnología |
|-----------|-----------|
| **Backend** | Python 3.12, Flask |
| **Base de datos** | ClickHouse (columnar OLAP) |
| **Visualización** | Grafana |
| **Contenedores** | Docker & Docker Compose |
| **ML** | scikit-learn, Prophet, pandas |
| **Autenticación** | JWT + bcrypt |
| **Cloud** | Google Cloud (BigQuery, Cloud Run) |

---

## 🏗️ Arquitectura del Sistema

### Componentes principales

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub API                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │ (Fetch Events)
        ┌────────────▼─────────────┐
        │                          │
┌───────▼────────┐      ┌─────────▼────────┐
│  Python ETL    │      │ Sample Data Gen  │
│  (github_etl)  │      │ (Demo Mode)      │
└───────┬────────┘      └─────────┬────────┘
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼─────────────────┐
        │    Flask API (port 8001)     │
        │  - Auth endpoints            │
        │  - Data endpoints            │
        │  - ML endpoints              │
        └────────────┬─────────────────┘
                     │
        ┌────────────▼─────────────────┐
        │   ClickHouse (port 9001)     │
        │  - Raw events table          │
        │  - Materialized views        │
        │  - Forecast tables           │
        └────────────┬─────────────────┘
                     │
        ┌────────────▼─────────────────┐
        │    Grafana (port 3001)       │
        │  - Dashboards               │
        │  - Visualizations            │
        └──────────────────────────────┘
```

### Flujo de datos

1. **Ingesta**: ETL extrae eventos de GitHub cada N minutos
2. **Almacenamiento**: Se guardan en tabla `github_analytics.events` en ClickHouse
3. **Procesamiento**: ML genera predicciones y clasificaciones
4. **Consulta**: API Flask expone endpoints para clientes
5. **Visualización**: Grafana carga datos vía API de ClickHouse

### Tabla de base de datos principal

```sql
CREATE TABLE github_analytics.events (
    id String,
    type String,
    actor_login String,
    repo_name String,
    created_at DateTime,
    payload String,
    url String
) ENGINE = MergeTree()
ORDER BY (created_at, repo_name);
```

---

## 📋 Requisitos Previos

### Sistema operativo

- Linux (WSL2 en Windows) o macOS
- 8GB RAM mínimo
- 20GB almacenamiento disponible

### Software requerido

```bash
# Verificar versiones necesarias
Python 3.12+
Docker 20.10+
Docker Compose 2.0+
Git 2.30+
```

### Credenciales y tokens

1. **GitHub Token** (opcional para demo)
   - Crear en: https://github.com/settings/tokens
   - Permisos mínimos: `repo`, `read:user`
   - Guardarlo en `.env` como `GITHUB_TOKEN`

2. **Google Cloud** (solo para BigQuery export)
   - Service Account JSON en `credentials/`
   - Variable: `GOOGLE_APPLICATION_CREDENTIALS`

### Verificar environment

```bash
# Ejecutar check
make check-env

# Debe confirmar: Python ✓, Docker ✓, Docker Compose ✓
```

---

## 🚀 Instalación y Setup Inicial

### Opción 1: Setup Completo (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd github-analytics

# 2. Setup completo (instala dependencias, inicia containers, inicializa DB)
make setup

# 3. Crear usuario admin
make init-users

# 4. Generar datos de demostración
make generate-sample-data

# 5. Ejecutar ETL (opcional - requiere GITHUB_TOKEN)
# Primero configurar: export GITHUB_TOKEN=ghp_xxxxx
make run-etl

# 6. Entrenar modelo de clasificación
make train-model

# 7. Verificar salud del sistema
make health-check
```

### Opción 2: Setup Manual Paso a Paso

```bash
# 1. Crear entorno virtual
make venv
source venv/bin/activate

# 2. Instalar dependencias
make install

# 3. Iniciar containers Docker
make up

# 4. Inicializar base de datos
make init

# 5. Esperar 10-15 segundos a que ClickHouse esté listo
sleep 15

# 6. Crear usuarios
python scripts/init_users.py
```

### Opción 3: Demo Rápida (Menor que 2 minutos)

```bash
# Todo en uno: setup + demo con datos de ejemplo
make quick-start

# Esto iniciará:
# - ClickHouse en puerto 9001
# - Grafana en puerto 3001
# - Flask API en puerto 8001
# - Datos de ejemplo precargados
```

### Validación post-instalación

```bash
# Verificar contenedores
docker ps | grep github_analytics

# Probar acceso a ClickHouse
make health-check

# Probar acceso a Grafana
curl http://localhost:3001/api/health

# Probar API Flask
curl http://localhost:8001/api/health

# Ver logs si hay problemas
make logs
```

---

## ⚙️ Configuración

### Archivo `.env` principal

```bash
# Crear archivo .env en raíz del proyecto
cat > .env << EOF
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx  # Opcional, sin él usa demo mode
GITHUB_API_BASE_URL=https://api.github.com

# ClickHouse Configuration
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=github_analytics

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Scheduler (en minutos)
ETL_SCHEDULE_MINUTES=60
MODEL_RETRAINING_SCHEDULE_HOURS=24

# Google Cloud (para BigQuery export)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Rate Limiting (segundos entre requests)
GITHUB_RATE_LIMIT_DELAY=1
EOF
```

### Archivo `.env` para desarrollo

```bash
# .env.development
DEBUG=True
FLASK_ENV=development
LOG_LEVEL=DEBUG
DEMO_MODE=True  # Usar datos de prueba sin GitHub token
```

### Variables de entorno por servicio

#### ClickHouse
- Editado en: `config/clickhouse/users.xml`
- Usuarios y permisos configurables
- Puerto: 9000 (internal), 9001 (mapped)

#### Grafana
- Editado en: `docker-compose.yml` sección `grafana.environment`
- Admin password por defecto: `admin/admin` (cambiar en producción)
- Dashboards JSON en: `grafana/dashboards/`

#### Flask API
- Ver: `src/config/settings.py`
- Carga vars de `.env` automáticamente con `python-dotenv`

### Configuración de datasources en Grafana

```bash
# Automatizar setup de Grafana
make setup-grafana

# O manual:
# 1. Ir a http://localhost:3001
# 2. Ingresa: admin / admin
# 3. Configuration > Data Sources
# 4. Agregar ClickHouse datasource:
#    - Host: clickhouse (nombre del servicio en docker)
#    - Port: 9000
#    - Database: github_analytics
#    - User: default
```

---

## 🔄 Operaciones Diarias

### Inicio del sistema

```bash
# Opción 1: Inicia todo con una línea
make up

# Opción 2: Detallado
docker-compose -f docker-compose.yml up -d

# Verificar estado
make status
```

### Ejecutar ETL (extracción de datos)

```bash
# Opción 1: Una sola vez (full)
make run-etl

# Opción 2: Automático con scheduler (background)
make run-scheduler

# Script individual
python scripts/scheduled_etl.py
```

### Entrenar modelos

```bash
# Entrenar clasificador de issues
make train-model

# Auto-entrenar cada 24h (en background)
make run-scheduler
```

### Consultar datos vía API

```bash
# 1. Login y obtener JWT token
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# 2. Listar repositorios
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/repos

# 3. Actividad de un repo
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/repos/owner/repo-name/activity

# 4. Predicciones
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/predictions/owner/repo-name

# 5. Clasificar issue (ML)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Login fails","body":"Users cannot login"}' \
  http://localhost:8001/api/classify
```

### Consultar datos directamente en ClickHouse

```bash
# Via cliente Python
python -c "
from src.database.clickhouse import clickhouse_client
result = clickhouse_client.execute_query(
    'SELECT COUNT(*) FROM github_analytics.events'
)
print(result)
"

# Via CLI (si está instalado clickhouse-client)
clickhouse-client -h localhost -p 9000 \
  -q "SELECT COUNT(*) FROM github_analytics.events"
```

### Ver logs

```bash
# Todos los servicios
make logs

# Solo ClickHouse
make logs-clickhouse

# Solo Grafana
make logs-grafana

# Flask API (en terminal separada)
python run.py

# Scheduler (en terminal separada)
make run-scheduler
```

---

## 🔧 Mantenimiento

### Limpieza de datos antiguos

```bash
# Ver tamaño de tabla events
python -c "
from src.database.clickhouse import clickhouse_client
result = clickhouse_client.execute_query(
    \"SELECT table, formatReadableSize(sum(bytes)) as size \"
    \"FROM system.parts \"
    \"WHERE database='github_analytics' \"
    \"GROUP BY table\"
)
for row in result:
    print(f'{row[0]}: {row[1]}')
"

# Eliminar eventos con más de 90 días
python -c "
from src.database.clickhouse import clickhouse_client
clickhouse_client.execute_query(
    \"ALTER TABLE github_analytics.events DELETE \"
    \"WHERE created_at < now() - interval 90 day\"
)
print('Deleted events older than 90 days')
"
```

### Reentrenamiento de modelos

```bash
# Entrenar con datos más recientes
make train-model

# Automático cada 24 horas
make run-scheduler &

# Ver modelo entrenado
ls -lh models/issue_classifier.pkl
```

### Actualizar dependencias

```bash
# Ver dependencias desactualizado
pip list --outdated

# Actualizar todo
pip install --upgrade -r requirements.txt

# Probar cambios
make test

# Reiniciar servicios
make restart
```

### Compactación de datos en ClickHouse

```bash
# Forzar merge de particiones
python -c "
from src.database.clickhouse import clickhouse_client
clickhouse_client.execute_query(
    'OPTIMIZE TABLE github_analytics.events FINAL'
)
print('Compaction started')
"

# Esperar 5-10 minutos para que termine
```

### Backup de base de datos

```bash
# Exportar tabla completa a CSV
python -c "
from src.database.clickhouse import clickhouse_client
result = clickhouse_client.execute_query(
    'SELECT * FROM github_analytics.events'
)
with open('backup_events.csv', 'w') as f:
    for row in result:
        f.write(','.join(map(str, row)) + '\n')
"

# Exportar a JSON
python scripts/export_to_bigquery.py --format json
```

---

## 🐛 Solución de Problemas

### Problema: Contenedores no inician

```bash
# Diagnosticar
docker-compose logs clickhouse grafana

# Soluciones comunes
docker-compose down -v    # Limpiar volumes
make clean
make setup

# Ver logs detallados
docker logs clickhouse_github_analytics
docker logs grafana_github_analytics
```

### Problema: ClickHouse no responde

```bash
# Verificar que está corriendo
docker ps | grep clickhouse

# Revisar logs
make logs-clickhouse

# Reiniciar
docker restart clickhouse_github_analytics

# Verificar puerto
netstat -tulpn | grep 9000 || ss -tulpn | grep 9000

# Prueba de conexión
python -c "
from src.database.clickhouse import clickhouse_client
try:
    result = clickhouse_client.execute_query('SELECT 1')
    print('✓ Conexión OK')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

### Problema: Grafana no se conecta a ClickHouse

```bash
# 1. Verificar datasource está bien configurado
curl http://localhost:3001/api/datasources

# 2. Probar conexión manualmente
curl -X POST http://localhost:3001/api/datasources/test \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ClickHouse",
    "type": "clickhouse",
    "url": "http://clickhouse:8123",
    "database": "github_analytics"
  }'

# 3. Si falla, revisar docker network
docker network inspect github_analytics_net

# 4. Usar host.docker.internal en Mac/Windows
# En datasource URL: http://host.docker.internal:8124
```

### Problema: ETL falla con "GitHub API rate limit exceeded"

```bash
# Esperar 1 hora o verificar token
echo $GITHUB_TOKEN

# Si está vacío, usar demo mode
export DEMO_MODE=True
make run-etl

# Si el token sigue siendo inválido
# 1. Regenerarlo en https://github.com/settings/tokens
# 2. Actualizar .env
# 3. source .env
```

### Problema: Token JWT inválido en API

```bash
# Regenerar token
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Verificar que se genera
echo $TOKEN

# Si falla, reiniciar API
make restart
```

### Problema: Entorno virtual corrupto

```bash
# Reparar automáticamente
make venv-fix

# O manual
rm -rf venv/
make venv
source venv/bin/activate
make install
```

### Problema: Permiso denegado en Docker

```bash
# En Linux, agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# O ejecutar con sudo
sudo make up
```

### Problema: Puerto ya en uso

```bash
# Ver qué proceso ocupa el puerto
lsof -i :8001  # Flask
lsof -i :9001  # ClickHouse
lsof -i :3001  # Grafana

# Liberar puerto (CUIDADO - mata procesos)
fuser -k 8001/tcp

# O cambiar puerto en docker-compose.yml
# Y en .env: CLICKHOUSE_PORT=9002
```

### Logs útiles para debugging

```bash
# Logs de todas las operaciones
tail -f ~/.logs/github-analytics.log

# Dentro de los containers
docker exec clickhouse_github_analytics \
  tail -f /var/log/clickhouse-server/clickhouse-server.log

# API Flask (console output)
python run.py  # Verás logs en tiempo real

# Sistema
dmesg | tail -20  # Errores del kernel
```

---

## 💾 Backup y Recuperación

### Estrategia de backup

```
Frecuencia: Diaria
Retención: 30 días
Ubicación: /backups/
Validación: Restauración semanal
```

### Script de backup automático

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/github-analytics"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio
mkdir -p $BACKUP_DIR

# Exportar datos de ClickHouse
docker exec clickhouse_github_analytics \
  clickhouse-client -q \
  "SELECT * FROM github_analytics.events 
   FORMAT Native" > $BACKUP_DIR/events_$DATE.ch

# Exportar modelos ML
tar -czf $BACKUP_DIR/models_$DATE.tar.gz models/

# Exportar configuración
cp .env $BACKUP_DIR/env_$DATE.backup
cp docker-compose.yml $BACKUP_DIR/docker-compose_$DATE.backup

# Limpiar backups antiguos (>30 días)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completado en $BACKUP_DIR"
```

### Ejecutar backup

```bash
# Manual
bash backup.sh

# O automático con cron (ejecutar cada día a las 02:00)
0 2 * * * /path/to/backup.sh >> /var/log/github-analytics-backup.log 2>&1
```

### Restaurar desde backup

```bash
# 1. Listar backups disponibles
ls -lh /backups/github-analytics/

# 2. Restaurar datos (ejemplo con archivo del 2026-06-03)
docker exec clickhouse_github_analytics \
  clickhouse-client -q \
  "INSERT INTO github_analytics.events FORMAT Native" \
  < /backups/github-analytics/events_20260603_020000.ch

# 3. Restaurar modelos
tar -xzf /backups/github-analytics/models_20260603_020000.tar.gz \
  -C ./

# 4. Validar integridad
make health-check
```

### Validar integridad de backups

```bash
# Verificar tamaño
ls -lh /backups/github-analytics/ | tail -5

# Probar restauración en entorno de prueba
docker-compose -f docker-compose.test.yml up -d
# Restaurar datos...
make test
```

---

## 📈 Escalabilidad

### Crecer en datos

**Problema:** Tabla `events` crece rápidamente (GB/día)

**Soluciones:**

1. **Particionamiento temporal**
```bash
# Ya implementado en create table, verifica:
python -c "
from src.database.clickhouse import clickhouse_client
result = clickhouse_client.execute_query(
    'SELECT partition, count() as rows FROM system.parts 
     WHERE database=\"github_analytics\" AND table=\"events\" 
     GROUP BY partition ORDER BY partition'
)
for row in result:
    print(row)
"
```

2. **Archivado de datos antiguos**
```bash
# Mover eventos >90 días a tabla de archive
# Implementar política de TTL en ClickHouse
python scripts/archive_old_events.py
```

3. **Compresión**
```bash
# Ya usada: LZ4 compression en ClickHouse
# Para más: cambiar en config.xml a Zstd
```

### Crecer en consultas

**Problema:** API lenta con muchos usuarios

**Soluciones:**

1. **Caché Redis** (agregar)
```bash
# Modificar docker-compose.yml
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"

# Usar en Flask para caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

2. **Materialized Views** (ya hay)
```bash
# Verificar vistas existentes
python -c "
from src.database.clickhouse import clickhouse_client
result = clickhouse_client.execute_query(
    \"SELECT name FROM system.tables 
     WHERE database='github_analytics' AND engine LIKE '%View%'\"
)
for row in result:
    print(row[0])
"
```

3. **Horizontal scaling** (Replica de ClickHouse)
```yaml
# docker-compose.yml - agregar
clickhouse-replica:
  image: clickhouse/clickhouse-server:latest
  environment:
    CLICKHOUSE_DB: github_analytics
  ports:
    - "9002:9000"
```

### Crecer en procesos

**Problema:** ETL tarda mucho

**Soluciones:**

1. **Paralelizar fetch**
```bash
# Modificar github_etl.py
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=5) as executor:
    # Fetch múltiples repos simultáneamente
```

2. **Batch insert** (ya optimizado)
```bash
# Verificar tamaño de batch en etl/github_etl.py
BATCH_SIZE = 10000
```

---

## 🔐 Seguridad

### Hardening de producción

#### 1. Cambiar credenciales por defecto

```bash
# ❌ NO usar en producción
# admin/admin (Grafana)
# empty password (ClickHouse)

# ✓ Cambiar passwords

# Grafana
docker exec grafana_github_analytics \
  grafana-cli admin set-password <new-password>

# ClickHouse - editar config/clickhouse/users.xml
<users>
  <default>
    <password_sha256_hex>...</password_sha256_hex>
  </default>
</users>

# JWT Secret - CRÍTICO
echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

#### 2. Habilitar HTTPS/TLS

```bash
# Generar certificado auto-firmado
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# En Flask (run.py)
app.run(ssl_context=('cert.pem', 'key.pem'))

# O con gunicorn (producción)
gunicorn --certfile=cert.pem --keyfile=key.pem \
  --bind 0.0.0.0:8001 wsgi:app
```

#### 3. Network policies

```bash
# Solo expose puertos necesarios
# En docker-compose.yml, usar solo internal network

services:
  clickhouse:
    networks:
      - github_analytics_net
    # No exponer puerto 9000 al host en producción
```

#### 4. Validación de inputs

```bash
# Ya implementado en Flask, verificar:
# - src/auth/decorators.py
# - src/auth/middleware.py

# Agregar rate limiting
from flask_limiter import Limiter
limiter = Limiter(app)

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    ...
```

#### 5. Auditoría

```bash
# Loguear accesos
# En src/utils/logger.py - agregar handler de auditoría

import logging
audit_log = logging.getLogger('audit')
handler = logging.FileHandler('audit.log')
audit_log.addHandler(handler)

# Loguear cada acceso a API
audit_log.info(f"User {user} accessed {endpoint}")
```

#### 6. Secretos

```bash
# NO commitear .env al git
echo ".env" >> .gitignore

# Usar AWS Secrets Manager o Google Secret Manager en producción
# Ej con Google:
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
secret = client.access_secret_version(
    request={"name": "projects/PROJECT/secrets/GITHUB_TOKEN/versions/latest"}
)
GITHUB_TOKEN = secret.payload.data.decode('UTF-8')
```

#### 7. Regulares security scans

```bash
# Escanear dependencias por vulnerabilidades
pip install safety
safety check

# Escanear código
pip install bandit
bandit -r src/

# Actualizar dependencias regularmente
pip install --upgrade pip
pip list --outdated
```

---

## 📊 Monitoreo y Alertas

### Métricas clave

| Métrica | Umbral Alerta | Frecuencia Chequeo |
|---------|---------------|-------------------|
| Tamaño BD | > 500GB | Diario |
| Health API | Respuesta > 2s | 5 min |
| Tasa eventos | < 100/hora | Cada 30 min |
| Modelos antiguos | > 7 días | Diario |
| ClickHouse CPU | > 80% | Cada 2 min |

### Health checks

```bash
# Sistema completo
make health-check

# Individual
curl http://localhost:8001/api/health
curl http://localhost:3001/api/health
docker exec clickhouse_github_analytics \
  clickhouse-client -q "SELECT 1"
```

### Dashboard de monitoreo

Crear en Grafana:

```
1. State of system (CPU, Memory)
   Query: SELECT * FROM system.processes LIMIT 1

2. Events per hour
   Query: SELECT toStartOfHour(created_at) as hour, count()
          FROM events GROUP BY hour

3. API response time
   Query: SELECT endpoint, avg(response_time_ms) FROM api_logs 
          GROUP BY endpoint

4. Model staleness
   Query: SELECT max(trained_at) FROM models
```

### Alertas en Grafana

```bash
# 1. Ir a http://localhost:3001/alerting/notification-channels
# 2. Agregar canal (Email, Slack, PagerDuty)
# 3. Crear alertas por dashboard

# Ejemplo Slack:
# Condition: when query(A) is above 1000
# Then: notify Slack channel #alerts
```

### Logs centralizados

Agregador de logs (opcional pero recomendado):

```yaml
# Agregar a docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log
    - /var/lib/docker/containers:/var/lib/docker/containers
```

---

## 🚨 Procedimientos de Respuesta a Incidentes

### Clasificación de severidad

| Severidad | Descripción | Respuesta | Escalación |
|-----------|------------|-----------|-----------|
| P1 | Sistema no disponible | 15 min | DevOps Lead |
| P2 | Funcionalidad reducida | 30 min | Tech Lead |
| P3 | Bug menor | 4 horas | Backlog |

### Playbooks

#### P1: API no responde

```bash
# 1. Verificar proceso
docker ps | grep predictions-api

# 2. Si no está, reiniciar
docker-compose restart predictions-api

# 3. Ver logs
docker logs predictions-api

# 4. Si falla, revisar ClickHouse
docker ps | grep clickhouse
docker logs clickhouse_github_analytics

# 5. Si todo falla, rollback
git log --oneline | head -5
git revert <commit>
make restart

# 6. Post-incidente
# Documentar causa en https://github.com/org/repo/issues/new
# Assignar follow-up
```

#### P2: ClickHouse lentitud

```bash
# 1. Revisar métricas
docker exec clickhouse_github_analytics \
  clickhouse-client -q "SHOW PROCESSLIST"

# 2. Matar queries largas si es necesario
docker exec clickhouse_github_analytics \
  clickhouse-client -q "KILL QUERY WHERE elapsed > 300"

# 3. Compactar
docker exec clickhouse_github_analytics \
  clickhouse-client -q "OPTIMIZE TABLE events FINAL"

# 4. Si sigue lento, revisar disk I/O
docker stats clickhouse_github_analytics
```

#### P3: Modelo no se entrena

```bash
# 1. Ver logs de scheduler
tail -f scheduler.log

# 2. Revisar datos de entrenamiento
python -c "
from src.models.github_models import load_training_data
data = load_training_data()
print(f'Rows: {len(data)}')
"

# 3. Re-entrenar
make train-model

# 4. Validar modelo
python -c "
import joblib
model = joblib.load('models/issue_classifier.pkl')
print(f'Model score: {model.score(X_test, y_test)}')
"
```

### Comunicación de incidentes

```
Plantilla de status update:

🚨 INCIDENT: [Descripción breve]
⏰ Detectado: [hora]
⚠️ Impacto: [N usuarios afectados]
🔧 Acción: [Acciones tomadas]
📊 Status: [Investigando/Mitigando/Resuelto]
✅ Resolución esperada: [ETA]

Mantener actualizaciones c/15 min mientras sea P1
```

---

## 📚 Recursos Útiles

### Documentación

- [README.md](README.md) - Descripción del proyecto
- [docs/api_documentation.md](docs/api_documentation.md) - API endpoints
- ClickHouse docs: https://clickhouse.com/docs/
- Grafana docs: https://grafana.com/docs/grafana/latest/

### Comandos frecuentes

```bash
# Reiniciar todo limpiamente
make clean && make setup

# Ver estado en vivo
watch -n 5 'make status'

# Monitorear logs
watch -n 1 'docker logs clickhouse_github_analytics | tail -20'

# Backup rápido
tar -czf backup_$(date +%s).tar.gz models/ .env

# Limpiar datos de prueba
docker exec clickhouse_github_analytics \
  clickhouse-client -q "TRUNCATE github_analytics.events"
```

### Contactos y escalación

```
Slack Channel: #github-analytics
On-Call: @devops-team
PagerDuty: [link]
Documentation: [wiki]
Runbook: RUNBOOK.md (este archivo)
```

### Control de versiones

```bash
# Versión actual
grep "version" package.json || echo "Ver git tags"
git describe --tags

# Historial de cambios
git log --oneline -10

# Cambios en la rama
git diff main
```

---

## 📝 Plantilla de Cambios

Siempre que realices cambios importantes:

```markdown
## Cambio realizado

**Fecha:** 2026-06-03
**Realizado por:** [tu nombre]
**Ticket:** [#123]

### Cambio
- Qué se modificó

### Razón
- Por qué se hizo

### Validación
- Cómo se verificó

### Rollback (si aplica)
- Cómo revertir

### Impacto
- Qué se vio afectado
```

---

## 📞 Contacto y Soporte

**Maintainers:**
- DevOps: @devops-team
- Backend: @backend-team

**Recursos:**
- GitHub Issues: [repo/issues](https://github.com/repo/issues)
- Slack: #github-analytics
- Docs: /docs

---

**Última revisión:** Junio 2026  
**Próxima revisión:** Septiembre 2026  
**Versión del runbook:** 1.0
