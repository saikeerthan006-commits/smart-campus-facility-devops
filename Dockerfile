# Stage 1: Dependency Builder
FROM python:3.12-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Hardened Non-Root Runtime Image
FROM python:3.12-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////app/data/campus_platform.db \
    APP_VERSION=v1.0.0

RUN groupadd -r campusgrp && useradd -r -g campusgrp -d /app -s /sbin/nologin campusapp && \
    mkdir -p /app/data && chown -R campusapp:campusgrp /app

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY --chown=campusapp:campusgrp campus_model.py /app/campus_model.py
COPY --chown=campusapp:campusgrp app /app/app
COPY --chown=campusapp:campusgrp migrations /app/migrations
COPY --chown=campusapp:campusgrp scripts /app/scripts

USER campusapp
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
