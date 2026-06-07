#!/bin/bash
# scripts/setup_metabase.sh
set -e

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

MB_URL=${MB_URL:-http://localhost:3000}
MB_ADMIN_EMAIL=${MB_ADMIN_EMAIL:-admin@metabase.com}
MB_ADMIN_PASSWORD=${MB_ADMIN_PASSWORD:-admin123}
MB_DB_NAME=${MB_DB_NAME:-GitHub Analytics ClickHouse}

CLICKHOUSE_HOST=${CLICKHOUSE_HOST_METABASE:-clickhouse}
CLICKHOUSE_PORT=${CLICKHOUSE_PORT_METABASE:-8123}
CLICKHOUSE_DB=${CLICKHOUSE_DATABASE_METABASE:-github_analytics}
CLICKHOUSE_USER=${METABASE_CLICKHOUSE_USER:-metabase_user}
CLICKHOUSE_PASS=${METABASE_CLICKHOUSE_PASSWORD:-secure_password_here}

# Esperar a que Metabase esté listo
echo "Waiting for Metabase to be ready..."
until curl -s -f "$MB_URL/api/health" > /dev/null; do
    sleep 2
done

# Configurar admin (idempotente)
echo "Setting up admin account..."
curl -s -X POST "$MB_URL/api/setup" \
  -H "Content-Type: application/json" \
  -d "{
    \"user\": {
      \"email\": \"$MB_ADMIN_EMAIL\",
      \"password\": \"$MB_ADMIN_PASSWORD\",
      \"first_name\": \"Admin\",
      \"last_name\": \"User\"
    },
    \"prefs\": {
      \"site_name\": \"GitHub Analytics\",
      \"allow_tracking\": false
    },
    \"database\": null
  }" > /dev/null

# Obtener token de sesión
TOKEN=$(curl -s -X POST "$MB_URL/api/session" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$MB_ADMIN_EMAIL\",\"password\":\"$MB_ADMIN_PASSWORD\"}" \
  | jq -r '.id')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Failed to obtain Metabase session token."
    exit 1
fi

# Comprobar si la base de datos ya está añadida
DB_EXISTS=$(curl -s -X GET "$MB_URL/api/database" \
  -H "X-Metabase-Session: $TOKEN" \
  | jq ".[] | select(.name == \"$MB_DB_NAME\") | .id")

if [ -z "$DB_EXISTS" ]; then
    echo "Adding ClickHouse database to Metabase..."
    curl -s -X POST "$MB_URL/api/database" \
      -H "Content-Type: application/json" \
      -H "X-Metabase-Session: $TOKEN" \
      -d "{
        \"name\": \"$MB_DB_NAME\",
        \"engine\": \"clickhouse\",
        \"details\": {
          \"host\": \"$CLICKHOUSE_HOST\",
          \"port\": $CLICKHOUSE_PORT,
          \"dbname\": \"$CLICKHOUSE_DB\",
          \"user\": \"$CLICKHOUSE_USER\",
          \"password\": \"$CLICKHOUSE_PASS\"
        },
        \"is_full_sync\": true
      }" > /dev/null
    echo "✅ Database added."
else
    echo "ℹ️ Database already exists. Skipping."
fi

echo "🎉 Metabase setup complete. Access at $MB_URL"