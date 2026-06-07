#!/bin/bash
# scripts/create_metabase_user.sh
set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Use docker-compose exec to run commands inside the running clickhouse service
# (this works regardless of container name)
echo "Creating dedicated Metabase user in ClickHouse..."

docker-compose exec -T clickhouse clickhouse-client --query "
CREATE USER IF NOT EXISTS '${METABASE_CLICKHOUSE_USER:-metabase_user}' 
IDENTIFIED BY '${METABASE_CLICKHOUSE_PASSWORD:-secure_password_here}';
GRANT SELECT ON ${CLICKHOUSE_DATABASE_METABASE:-github_analytics}.* 
TO '${METABASE_CLICKHOUSE_USER:-metabase_user}';
"

echo "✅ Metabase user '${METABASE_CLICKHOUSE_USER:-metabase_user}' created/verified."