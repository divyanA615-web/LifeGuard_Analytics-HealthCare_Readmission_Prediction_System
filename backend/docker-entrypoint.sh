#!/bin/sh
set -e

# If DATABASE_URL is not set, try to construct from DB_* envs (for local simplicity)
if [ -z "$DATABASE_URL" ]; then
  if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ] && [ -n "$DB_NAME" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ]; then
    export DATABASE_URL="postgresql+psycopg2://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    echo "Constructed DATABASE_URL from DB_* env vars"
  else
    echo "DATABASE_URL not set and DB_* vars incomplete – backend may fail to connect"
  fi
fi

# Optionally run alembic migrations if MIGRATE_ON_START=1
if [ "$MIGRATE_ON_START" = "1" ]; then
  echo "Running database migrations..."
  alembic upgrade head || true
fi

# Dump effective config for debug (avoid leaking secrets)
echo "Starting backend with:"
echo "  ENVIRONMENT=${ENVIRONMENT:-dev}"
echo "  DEPLOY_ENV=${DEPLOY_ENV:-dev}"

# Wait for model artifacts on Render Disk (empty on first boot)
if [ ! -f "$MODEL_ARTIFACT_PATH/model.onnx" ]; then
  echo "Model artifact not baked; fetching from disk mount (Render persistent whatever)"
  mkdir -p "$MODEL_ARTIFACT_PATH"
  # If MODEL_S3_URI provided, sync from remote; otherwise leave empty => service will
  # mark readiness as degraded / calls return 503 until weights are available.
  if [ -n "$MODEL_S3_URI" ]; then
    pip install awscli >/dev/null 2>&1
    aws s3 sync "$MODEL_S3_URI" "$MODEL_ARTIFACT_PATH" --no-progress
  fi
fi

exec "$@"
