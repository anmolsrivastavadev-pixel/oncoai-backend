# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
# INSTALL_ML=0 builds a small image that uses the CV-only heuristic analyzer.
ARG INSTALL_ML=1
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_ML" = "1" ]; then \
         pip install --index-url https://download.pytorch.org/whl/cpu torch==2.15.0 \
         && pip install -r requirements-ml.txt; \
       fi

COPY . .
RUN useradd --system --create-home --uid 10001 oncoai \
    && mkdir -p /data/uploads /data/models \
    && chown -R oncoai:oncoai /data /app \
    && chmod +x docker-entrypoint.sh
# The entrypoint starts as root only to fix ownership of the mounted /data volume
# (hosts mount volumes root-owned), then drops to the unprivileged oncoai user.

ENV UPLOAD_DIR=/data/uploads MODEL_DIR=/data/models/skin-lesion-vit
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fsS "http://localhost:${PORT:-8000}/health" || exit 1
ENTRYPOINT ["./docker-entrypoint.sh"]
# PORT is injected by most container hosts. Set FORWARDED_ALLOW_IPS only when the
# container sits behind a trusted proxy, so client IPs (used for rate limits) are right.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
