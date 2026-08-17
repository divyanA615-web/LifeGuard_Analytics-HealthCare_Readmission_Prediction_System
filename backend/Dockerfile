# syntax=docker/dockerfile:1.6

FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libgomp1 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

ARG DEPLOY_ENV=prod
ENV DEPLOY_ENV=$DEPLOY_ENV \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080

HEALTHCHECK CMD python -c "import os, urllib.request, sys; port=os.environ.get('PORT','8080'); sys.exit(urllib.request.urlopen(f'http://localhost:{port}/v1/health').status != 200)"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --log-level info"]
