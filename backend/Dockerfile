# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app

ARG DEPLOY_ENV=prod
ENV DEPLOY_ENV=$DEPLOY_ENV \
    PATH=/home/appuser/.local/bin:/usr/local/bin:/usr/bin:/bin \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --shell /usr/sbin/nologin --home /app appuser

COPY --chown=appuser:appuser --from=builder /home/appuser/.local /home/appuser/.local
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER appuser

EXPOSE 8080

HEALTHCHECK CMD python -c "import urllib.request, sys; sys.exit(urllib.request.urlopen('http://localhost:8080/v1/health').status != 200)"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--log-level", "info"]
